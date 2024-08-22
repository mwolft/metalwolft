"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users, Ingredients
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity


api = Blueprint('api', __name__)
CORS(api)


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


@api.route('/ingredients/<int:ingredient_id>', methods=['GET'])
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


@api.route('/ingredients/<int:ingredient_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def handle_edit_ingredient(ingredient_id):
    response_body = {}
    current_user = get_jwt_identity()    
    if request.method == 'PUT':
        if (current_user.rol == "user"):
            response_body['message'] = 'Authorization denied'
            return response_body, 401
        data = request.get_json()
        ingredient = db.session.execute(db.select(Ingredients).where(Ingredients.id == ingredient_id)).scalar()
        if not ingredient:
            response_body['results'] = {}
            response_body['message'] = f'Ingredient {ingredient_id} not exist'
            return response_body, 404
        ingredient.name = data.get('name', ingredient.name )
        ingredient.energy = data.get('energy', ingredient.energy)
        ingredient.proteins = data.get('proteins', ingredient.proteins)
        ingredient.carbohydrates = data.get('carbohydrates', ingredient.carbohydrates)
        ingredient.fats = data.get('fats', ingredient.fats)
        ingredient.sugar = data.get('sugar', ingredient.sugar)
        # ingredient.license_object_url = data.get('license_object_url', ingredient.license_object_url)
        db.session.commit()
        response_body['results'] = ingredient.serialize()
        response_body['message'] = f'Ingredient {ingredient_id} updated'
        return response_body, 200
    if request.method == 'DELETE':
        if (current_user.rol == "user"):
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


@api.route('/ingredients', methods=['GET'])
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


@api.route('/ingredients', methods=['POST'])
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
        proteins = data.get('proteins, None')
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
