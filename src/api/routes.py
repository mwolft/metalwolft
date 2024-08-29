"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Ingredients, Recipes, Exercises, Muscles, Equipments, Favorites
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from groq import Groq
from dotenv import load_dotenv
import json
import os
import requests

load_dotenv()

api = Blueprint('api', __name__)

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

@api.route('/generate-recipe', methods=['GET'])
#  @jwt_required()
def generate_recipe():
    response_body = {}
    # Get the list of ingredient IDs from the query parameters
    ingredient_ids = request.args.get('ingredient_ids')
    if not ingredient_ids:
        response_body['message'] = 'No ingredient IDs provided'
        return jsonify(response_body), 400
    # Convert the string of IDs into a list of integers
    ingredient_ids = list(map(int, ingredient_ids.split(',')))
    # Fetch ingredient details from the database
    ingredients = db.session.execute(
        db.select(Ingredients).where(Ingredients.id.in_(ingredient_ids))
    ).scalars().all()
    if not ingredients:
        response_body['message'] = 'No valid ingredients found'
        return jsonify(response_body), 404
    # Create a list of ingredient names
    ingredient_names = [ingredient.name for ingredient in ingredients]
    # Structure of the prompt for recipe
    prompt = (f"Create a healthy recipe using the following ingredients: {', '.join(ingredient_names)}. "
              f"The recipe should be nutritious and balanced. Include the total nutritional information: proteins, calories, and fats "
              f"And return the response in json ")
    try:
        # Use Groq to generate a recipe based on the ingredients
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a helpful trainer"},
                      {"role": "user", "content": prompt}],
            model="llama3-8b-8192",)
        generated_text = chat_completion.choices[0].message.content
        response_body['ingredients'] = [ingredient.serialize() for ingredient in ingredients]
        response_body['generated_recipe'] = generated_text
        response_body['message'] = 'Healthy recipe generated successfully'
        return jsonify(response_body), 200
    except Exception as e:
        response_body['message'] = f'An error occurred while generating the recipe: {str(e)}'
        return jsonify(response_body), 500


@api.route('/generate-exercise-routine', methods=['POST'])
# @jwt_required()
def generate_exercise_routine():
    response_body = {}
    data = request.json
    # Extract parameters from request body
    days = data.get('days', None)
    hours_per_day = data.get('hours_per_day', None)
    target_muscles = data.get('target_muscles', None)
    # Validate parameters
    if not days or not hours_per_day or not target_muscles:
        response_body['message'] = 'Days, hours per day, and target muscles are required'
        return jsonify(response_body), 400
    # Fetch exercises that target the specified muscles
    exercises = db.session.execute(
        db.select(Exercises).where(Exercises.muscle.in_(target_muscles))
    ).scalars().all()
    if not exercises:
        response_body['message'] = 'No exercises found for the specified muscles'
        return jsonify(response_body), 404 
    # Create a prompt for the routine generation
    prompt = (f"Generate a workout routine based on the following parameters: "
              f"Days available: {days}, "
              f"Hours available per day: {hours_per_day}, "
              f"Targeted muscles: {', '.join(target_muscles)}. "
              f"Provide a balanced routine that fits within the specified days and hours, "
              f"and includes a variety of exercises to target the mentioned muscles. "
              f"Return the routine in JSON format.")  
    try:
        # Use Groq to generate a workout routine based on the parameters
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": "You are a fitness coach"},
                      {"role": "user", "content": prompt}],
            model="llama3-8b-8192",)
        generated_text = chat_completion.choices[0].message.content
        response_body['parameters'] = {
            'days': days,
            'hours_per_day': hours_per_day,
            'target_muscles': target_muscles}
        response_body['generated_routine'] = generated_text
        response_body['message'] = 'Workout routine generated successfully'
        return jsonify(response_body), 200
    except Exception as e:
        response_body['message'] = f'An error occurred while generating the routine: {str(e)}'
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
    user = Users()
    user.email = email
    user.password = password
    user.rol = "user"
    db.session.add(user)
    db.session.commit()
    access_token = create_access_token(identity={'email': user.email,
                                                 'user_id': user.id,
                                                 'rol': user.rol}) 
    response_body['results'] = user.serialize()
    response_body['message'] = 'User registrado y logeado'
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
def handle_user(user_id):
    response_body = {}
    if request.method == 'GET':
        row = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not row:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        response_body['results'] = row.serialize()
        response_body['message'] = f'recibí el GET request {user_id}'
        return response_body, 200
    if request.method == 'PUT':
        data = request.get_json()
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.firstname = data.get('firstname', user.firstname)
        user.lastname = data.get('lastname', user.lastname)
        db.session.commit()
        response_body['results'] = user.serialize()
        response_body['message'] = f'Usuario {user_id} actualizado'
        return response_body, 200
    if request.method == 'DELETE':
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        db.session.delete(user)
        db.session.commit()
        response_body['message'] = f'Usuario {user_id} eliminado'
        return response_body, 200


@api.route('/exercise/<int:ingredient_id>', methods=['GET'])
def handle_ingredient(ingredient_id):
     response_body = {}
     if request.method == 'GET':
         row = db.session.execute(db.select(Ingredients).where(Ingredients.id == ingredient_id)).scalar()
         if not row:
             response_body['results'] = {}
             response_body['message'] = f'Ingredient {ingredient_id} not exist'
             return response_body, 404
         response_body['results'] = row.serialize()
         response_body['message'] = f'Ingredient {ingredient_id} recieved'
         return response_body, 200


@api.route('/exercise', methods=['GET'])
def handle_ingredients():
    response_body = {}
    if request.method == 'GET':
        rows = db.session.execute(db.select(Ingredients)).scalars()
        results = []
        for row in rows:
            results.append(row.serialize())
        response_body['results'] = results
        response_body['message'] = "Ingredient list"
        return response_body, 200


@api.route('/exercise', methods=['POST'])
@jwt_required()
def handle_add_ingredients():
    response_body = {}
    current_user = get_jwt_identity()    
    if request.method == 'POST':
        if (current_user.rol == "user"):
            response_body['message'] = 'Authorization denied'
            return response_body, 401
        data = request.json
        name = data.get('name', None)
        kcal = data.get('kcal', None)
        proteins = data.get('proteins', None)
        carbohydrates = data.get('carbohydrates', None)
        fats = data.get('fats', None)
        sugar = data.get('sugar', None)
        if not name:
            response_body['message'] = 'Missing ingredient name'
            response_body['results'] = {}
            return response_body, 400
        ingredient_name_exist = db.session.execute(db.select(Ingredients).where(Ingredients.name == name)).scalar()
        if ingredient_name_exist:
            response_body['message'] = 'Ingredient already exist'
            response_body['results'] = {}
            return response_body, 404
        row = Ingredients(name = data['name'],
                         energy = data['energy'],
                         proteins = data['proteins'],
                         carbohydrates = data['carbohydrates'],
                         fats = data['fats'],
                         sugar = data['sugar'])
        db.session.add(row)
        db.session.commit()
        response_body['message'] = "Ingredient added succesfully"
        response_body['results'] = row.serialize()
        return response_body, 200


@api.route('/temp-load-ingredients', methods=['GET'])
def load_ingredient():
    with open('src/api/Ingredients.json') as json_file:
        data = json.load(json_file)
    for row in data['ingredients']:
            ingredients = Ingredients()
            ingredients.calories = 1.0  # TODO: revisar esto
            ingredients.type = row['type']
            ingredients.name = row['name']
            ingredients.proteins = row['protein']
            ingredients.fat = row['fat']
            ingredients.carbs = row['carbs']
            ingredients.sugar = row['sugar']
            db.session.add(ingredients)
            db.session.commit()
    return jsonify(data), 200


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
                exercises = Exercises()
                exercises.name = row['name']
                exercises.description = row['description']
                db.session.add(exercises)
                db.session.commit()
    return response_body, 200


@api.route('/load-muscles', methods=['GET'])
def load_data_muscles_from_api():
    response_body = {}
    url = 'https://wger.de/api/v2/muscle/'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        response_body['results'] = data['results']
        for row in data['results']:
            existing_muscle = db.session.execute(db.select(Muscles).where(Muscles.name == row['name'])).scalar()
            if not existing_muscle:
                muscles = Muscles()
                muscles.name = row['name']
                db.session.add(muscles)
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


# Route to add a favorite recipe
@api.route('/add_favorite', methods=['POST'])
def add_favorite():
    data = request.get_json()
    user_id = data.get('user_id')
    recipe_id = data.get('recipe_id')
    if not user_id or not recipe_id:
        return jsonify({"error": "User ID and Recipe ID are required"}), 400
    # Check if the favorite already exists
    favorite = Favorites.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
    if favorite:
        return jsonify({"message": "Recipe already added to favorites"}), 200
    # Add the favorite
    new_favorite = Favorites(user_id=user_id, recipe_id=recipe_id)
    db.session.add(new_favorite)
    db.session.commit()
    return jsonify({"message": "Recipe added to favorites successfully"}), 201


# Route to remove a favorite recipe
@api.route('/remove_favorite', methods=['POST'])
def remove_favorite():
    data = request.get_json()
    user_id = data.get('user_id')
    recipe_id = data.get('recipe_id')
    if not user_id or not recipe_id:
        return jsonify({"error": "User ID and Recipe ID are required"}), 400
    favorite = Favorites.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
    if not favorite:
        return jsonify({"message": "Favorite not found"}), 404
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Recipe removed from favorites successfully"}), 200
