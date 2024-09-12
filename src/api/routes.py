"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Ingredients, Recipes, Exercises, ExerciseMuscles, Muscles, Equipments, Routines, Recipes, FavoriteRecipes, FavoriteRoutines, FavoriteExercises
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from groq import Groq
from dotenv import load_dotenv
import json
import os
import requests

load_dotenv()

api = Blueprint('api', __name__)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"),
)

@api.route('/generate-recipe', methods=['GET'])
def generate_recipe():
    response_body = {}
    ingredient_names = request.args.get('ingredient_names')
    if not ingredient_names:
        response_body['message'] = 'No ingredient names provided'
        return jsonify(response_body), 400
    ingredient_list = [name.strip() for name in ingredient_names.split(',')]
    prompt = (f"Create a healthy recipe using the following ingredients: {', '.join(ingredient_list)}. "
              f"The recipe should be nutritious and balanced. Include the total nutritional information: proteins, calories, and fats."
              f"Response with (Sorry this is not an ingredient) if the user sends anything not related to ingredients and nutrition."
              f"the response should not have this /\*\*(.*?)\*\*/g it has to be well presented for the viewers")
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful trainer"},
                      {"role": "user", "content": prompt}],
            model="llama3-8b-8192",)
        generated_text = chat_completion.choices[0].message.content
        ingredients_text = ", ".join(ingredient_list)
        recipe = Recipes(name="Generated Recipe", ingredients_text=ingredients_text)
        db.session.add(recipe)
        db.session.commit()
        response_body['generated_recipe'] = generated_text
        response_body['recipe_id'] = recipe.id 
        response_body['message'] = 'Healthy recipe generated successfully'
        return jsonify(response_body), 200
    except Exception as e:
        response_body['message'] = f'An error occurred while generating the recipe: {str(e)}'
        return jsonify(response_body), 500


@api.route('/generate-exercise-routine', methods=['POST'])
@jwt_required() 
def generate_exercise_routine():
    response_body = {}
    user_id = get_jwt_identity()['user_id'] 
    data = request.json
    days = data.get('days', None)
    hours_per_day = data.get('hours_per_day', None)
    target_muscles = data.get('target_muscles', None)
    level = data.get('level', None)
    if not days or not hours_per_day or not target_muscles or not level:
        response_body['message'] = 'Days, hours per day, target muscles, and level are required'
        return jsonify(response_body), 400
    valid_levels = ['beginner', 'intermediate', 'advanced']
    if level.lower() not in valid_levels:
        response_body['message'] = f'Invalid level. Valid options are: {", ".join(valid_levels)}'
        return jsonify(response_body), 400
    muscle_mapping = {'chest': 'chest', 'back': 'back', 'bicep': 'biceps', 'biceps': 'biceps',
                      'tricep': 'triceps', 'triceps': 'triceps', 'shoulder': 'shoulders', 'shoulders': 'shoulders',
                      'leg': 'legs', 'legs': 'legs'}
    normalized_muscles = [muscle_mapping.get(muscle.lower(), None) for muscle in target_muscles]
    if None in normalized_muscles:
        response_body['message'] = 'Invalid muscle names. Valid options are: chest, back, biceps, triceps, shoulders, legs'
        return jsonify(response_body), 400
    prompt = (f"Create a {level.lower()} workout routine for a person who has {days} days available and can work out {hours_per_day} hours per day. "
              f"The routine should focus on these muscles: {', '.join(normalized_muscles)}. "
              f"Include warm-ups and variety in exercises.")
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful fitness coach"},
                      {"role": "user", "content": prompt}],
            model="llama3-8b-8192",)
        generated_text = chat_completion.choices[0].message.content
        routine = Routines(user_id=user_id, prompt=generated_text)
        db.session.add(routine)
        db.session.commit()
        response_body['generated_routine'] = generated_text
        response_body['routine_id'] = routine.id  # Include dynamic routine ID
        response_body['message'] = 'Workout routine generated successfully'
        return jsonify(response_body), 200
    except Exception as e:
        response_body['message'] = f'Error generating routine: {str(e)}'
        return jsonify(response_body), 500


@api.route('/hello', methods=['GET'])
def handle_hello():
    response_body = {}
    response_body['message'] = "Hello! I'm a message that came from the backend, check the network tab on the google inspector and you will see the GET request"
    return response_body, 200


@api.route("/login", methods=["POST"])
def login():
    response_body = {}
    data = request.json
    email = data.get("email", None)
    password = data.get("password", None)
    user = db.session.execute(db.select(Users).where(Users.email == email, Users.password == password)).scalar()
    if not user:
        response_body['message'] = 'Authorization denied'
        return response_body, 401
    access_token = create_access_token(identity={'email': user.email, 
                                                 'user_id': user.id,
                                                 "rol": user.rol})
    response_body['results'] = user.serialize()
    response_body['message'] = 'Bienvenido'
    response_body['access_token'] = access_token
    return response_body, 201


@api.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    response_body = {}
    current_user = get_jwt_identity()  
    if current_user:
        response_body['message'] = f'Access granted {current_user["email"]}'
        response_body['results'] = current_user
        return response_body, 200
    response_body['message'] = f'Access denied'
    response_body['results'] = {}
    return response_body, 403


@api.route('/signup', methods=['POST'])
def signup():
    response_body = {}
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    # Check if the user already exists with the provided email
    existing_user = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
    if existing_user:
        response_body['message'] = 'User with this email already exists'
        return response_body, 409 
    user = Users()
    user.email = email
    user.password = password
    user.rol = "user"
    db.session.add(user)
    db.session.commit()
    access_token = create_access_token(identity={'email': user.email, 'user_id': user.id, 'rol': user.rol})
    response_body['results'] = user.serialize()
    response_body['message'] = 'User registered and logged in'
    response_body['access_token'] = access_token
    return response_body, 201


@api.route('/users', methods=['GET'])
def handle_users():
    response_body = {}
    if request.method == 'GET':
        rows = db.session.execute(db.select(Users)).scalars()
        results = []
        for row in rows:
            results.append(row.serialize())
        response_body['results'] = results
        response_body['message'] = "Lista de usuarios"
        return response_body, 200


@api.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()  
def handle_user(user_id):
    response_body = {}
    current_user = get_jwt_identity()  
    if current_user['user_id'] != user_id:
        return jsonify({"message": "No autorizado para modificar este perfil"}), 403
    if request.method == 'GET':
        row = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not row:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        response_body['results'] = row.serialize()
        response_body['message'] = f'Datos del usuario {user_id} obtenidos correctamente'
        return response_body, 200
    if request.method == 'PUT':
        data = request.get_json()
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        user.email = data.get('email', user.email)
        user.firstname = data.get('firstname', user.firstname)
        user.lastname = data.get('lastname', user.lastname)
        user.height = data.get('height', user.height)  
        user.weight = data.get('weight', user.weight)  
        user.age = data.get('age', user.age)
        user.location = data.get('location', user.location) 
        db.session.commit()  
        response_body['results'] = user.serialize()
        response_body['message'] = f'Usuario {user_id} actualizado exitosamente'
        return response_body, 200
    if request.method == 'DELETE':
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        db.session.delete(user)
        db.session.commit()
        response_body['message'] = f'Usuario {user_id} eliminado correctamente'
        return response_body, 200


@api.route('/upload-exercises', methods=['POST'])
def upload_exercises():
    try:
        exercises_file_path = os.path.join(os.path.dirname(__file__), 'Exercises.json')
        with open(exercises_file_path, 'r') as file:
            exercises_data = json.load(file)
        for exercise in exercises_data:
            existing_exercise = db.session.query(Exercises).filter_by(name=exercise['name']).first()
            if existing_exercise:
                print(f"Exercise '{exercise['name']}' already exists. Skipping insertion.")
                continue 
            new_exercise = Exercises(name=exercise['name'],
                                     description=exercise['description'],
                                     image_url=exercise.get('image_url', None))
            db.session.add(new_exercise)
            db.session.flush()
            muscle_names = exercise.get('muscle_group', [])
            for muscle_name in muscle_names:
                muscle = db.session.query(Muscles).filter_by(name=muscle_name).first()
                if muscle:
                    exercise_muscle = ExerciseMuscles(exercise_id=new_exercise.id, muscle_id=muscle.id)
                    db.session.add(exercise_muscle)
        db.session.commit()
        return jsonify({"message": "Exercises uploaded successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api.route('/exercises', methods=['GET'])
def get_exercise():
    muscle_group_filter = request.args.get('muscle_group')
    EXERCISES_JSON_PATH = os.path.join(os.path.dirname(__file__), 'Exercises.json')
    with open(EXERCISES_JSON_PATH) as file:
        exercises_data = json.load(file)
    if muscle_group_filter:
        filtered_exercises = [
            exercise for exercise in exercises_data
            if muscle_group_filter.lower() == exercise.get('muscle_group', '').lower()
        ]
        return jsonify(filtered_exercises), 200
    return jsonify(exercises_data), 200


@api.route('/temp-load-ingredients', methods=['GET'])
def load_ingredient():
    with open('src/api/Ingredients.json') as json_file:
        data = json.load(json_file)
    for row in data['ingredients']:
            ingredients = Ingredients()
            ingredients.calories = 1.0 
            ingredients.type = row['type']
            ingredients.name = row['name']
            ingredients.proteins = row['protein']
            ingredients.fat = row['fat']
            ingredients.carbs = row['carbs']
            ingredients.sugar = row['sugar']
            db.session.add(ingredients)
            db.session.commit()
    return jsonify(data), 200


@api.route('/ingredients', methods=['GET'])
def get_ingredients():
    ingredients = db.session.query(Ingredients).all()
    return jsonify([ingredient.serialize() for ingredient in ingredients]), 200


@api.route('/ingredients/<int:ingredient_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def handle_edit_ingredient(ingredient_id):
    response_body = {}
    current_user = get_jwt_identity()
    if request.method == 'PUT':
        if (current_user["rol"] == "user"):
            response_body['message'] = 'Authorization denied'
            return response_body, 401
        data = request.get_json()
        ingredient = db.session.execute(db.select(Ingredients).where(Ingredients.id == ingredient_id)).scalar()
        if not ingredient:
            response_body['results'] = {}
            response_body['message'] = f'Ingredient {ingredient_id} not exist'
            return response_body, 404
        ingredient.name = data.get('name', ingredient.name)
        ingredient.type = data.get('type', ingredient.type)
        ingredient.calories = data.get('calories', ingredient.calories)
        ingredient.proteins = data.get('proteins', ingredient.proteins)
        ingredient.carbs = data.get('carbs', ingredient.carbs)
        ingredient.fat = data.get('fat', ingredient.fat)
        ingredient.sugar = data.get('sugar', ingredient.sugar)
        db.session.commit()
        response_body['results'] = ingredient.serialize()
        response_body['message'] = f'Ingredient {ingredient_id} updated'
        return response_body, 200
    if request.method == 'DELETE':
        if (current_user["rol"] == "user"):
            response_body['message'] = 'Authorization denied'
            return response_body, 401
        ingredient = db.session.execute(db.select(Ingredients).where(Ingredients.id == ingredient_id)).scalar()
        if not ingredient:
            response_body['results'] = {}
            response_body['message'] = f'Ingredient {ingredient_id} not exist'
            return response_body, 404
        db.session.delete(ingredient)
        db.session.commit()
        response_body['message'] = f'Ingredient {ingredient_id} deleted'
        return response_body, 200


@api.route('/load-exercises', methods=['GET'])
def load_data_exercise_from_api():
    response_body = {}
    url = 'https://wger.de/api/v2/exercise/?limit=20&offset=20'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        response_body['results'] = data['results']  
        for row in data['results']:
            existing_exercise = db.session.execute(db.select(Exercises).where(Exercises.name == row['name'])).scalar()
            if not existing_exercise:
                new_exercise = Exercises()
                new_exercise.name = row['name']
                new_exercise.description = row['description']
                db.session.add(new_exercise)
                db.session.commit()
                print(f"Added exercise: {new_exercise.name}")
                if 'muscles' in row:
                    for muscle_id in row['muscles']:
                        existing_muscle = db.session.query(Muscles).filter_by(id=muscle_id).first()
                        if existing_muscle:
                            print(f"Associating {new_exercise.name} with muscle {existing_muscle.name}")
                            exercise_muscle = ExerciseMuscles(exercise_id=new_exercise.id, muscle_id=existing_muscle.id)
                            db.session.add(exercise_muscle)
                db.session.commit() 
            else:
                print(f"Exercise {row['name']} already exists")
    return response_body, 200


@api.route('/get-all-exercises', methods=['GET'])
def get_all_exercises():
    exercises = db.session.query(Exercises).all()
    return jsonify([exercise.serialize() for exercise in exercises]), 200


@api.route('/get-all-exercise-muscles', methods=['GET'])
def get_all_exercise_muscles():
    exercise_muscles = db.session.query(ExerciseMuscles).all()
    muscles = db.session.query(Muscles).all()
    return jsonify({
        "exercise_muscles": [em.serialize() for em in exercise_muscles],
        "muscles": [muscle.serialize() for muscle in muscles]
    }), 200


@api.route('/load-muscles', methods=['GET'])
def load_data_muscles_from_api():
    response_body = {}
    url = 'https://wger.de/api/v2/muscle/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        response_body['results'] = data['results']
        
        for row in data['results']:
            existing_muscle = db.session.query(Muscles).filter_by(name=row['name']).first()
            if not existing_muscle:
                # Add new muscle
                muscle = Muscles(name=row['name'])
                db.session.add(muscle)
                db.session.commit()
    return response_body, 200


@api.route('/load-equipment', methods=['GET'])
def load_data_equipments_from_api():
    response_body = {}
    url = 'https://wger.de/api/v2/equipment/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        response_body['results'] = data['results']
        for row in data['results']:
            existing_equipment = db.session.execute(db.select(Equipments).where(Equipments.name == row['name'])).scalar()
            if not existing_equipment:
                equipment = Equipments()
                equipment.name = row['name']
                db.session.add(equipment)
                db.session.commit()
    return response_body, 200


@api.route('/favorite-routine', methods=['POST'])
@jwt_required()
def favorite_routine():
    user_id = get_jwt_identity()['user_id']
    data = request.get_json()
    routine_id = data.get('routine_id')
    if not routine_id:
        return jsonify({"message": "Routine ID is required"}), 400
    routine = Routines.query.get(routine_id)
    if not routine:
        return jsonify({"message": "Routine not found"}), 404
    favorite = FavoriteRoutines(user_id=user_id, routine_id=routine_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"message": "Routine added to favorites successfully"}), 201


@api.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    user_id = get_jwt_identity()['user_id']
    favorite_recipes = FavoriteRecipes.query.filter_by(user_id=user_id).all()
    favorite_routines = FavoriteRoutines.query.filter_by(user_id=user_id).all()
    return jsonify({
        "recipes": [fav.recipe_id for fav in favorite_recipes],
        "routines": [fav.routine_id for fav in favorite_routines]
    }), 200


@api.route('/favorite-recipe', methods=['POST'])
@jwt_required()
def favorite_recipe():
    user_id = get_jwt_identity()['user_id']
    data = request.get_json() 
    # Ensure recipe_id is provided
    recipe_id = data.get('recipe_id')
    if not recipe_id:
        return jsonify({"message": "Recipe ID is required"}), 400
    # Check if the recipe exists
    recipe = Recipes.query.get(recipe_id)
    if not recipe:
        return jsonify({"message": "Recipe not found"}), 404
    # Check if the recipe is already in the user's favorites
    favorite = FavoriteRecipes.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
    if favorite:
        return jsonify({"message": "Recipe already in favorites"}), 400
    # Create a new favorite recipe entry
    favorite = FavoriteRecipes(user_id=user_id, recipe_id=recipe_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify({"message": "Recipe added to favorites successfully"}), 201


@api.route('/favorite-routine/<int:routine_id>', methods=['DELETE'])
@jwt_required() 
def delete_favorite_routine(routine_id):
    user_id = get_jwt_identity()['user_id']
    favorite = FavoriteRoutines.query.filter_by(user_id=user_id, routine_id=routine_id).first()
    if not favorite:
        return jsonify({"message": "Favorite routine not found"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Routine removed from favorites successfully"}), 200
