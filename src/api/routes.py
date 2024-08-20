"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
from flask import Flask, request, jsonify, url_for, Blueprint
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from api.models import db, Users
from flask_jwt_extended import create_access_token
from flask_jwt_extended import jwt_required
from flask_jwt_extended import get_jwt_identity


api = Blueprint('api', __name__)
CORS(api)  # Allow CORS requests to this API


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
                                                 'user_id': user.id})
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
        response_body['message'] = f'Acceso concedido a {current_user["email"]}'
        response_body['results'] = current_user
        return response_body, 200
    response_body['message'] = f'Acceso dengado'
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
    db.session.add(user)
    db.session.commit()
    access_token = create_access_token(identity={'email': user.email,
                                                 'user_id': user.id,}) 
    response_body['results'] = user.serialize()
    response_body['message'] = 'User registrado y logeado'
    response_body['access_token'] = access_token
    return response_body, 201


@api.route('/users', methods=['GET', 'POST'])
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
    if request.method == 'POST':
        data = request.json
        # Se intenta obtener los valores de username y email del diccionario data. 
        # Si alguna de estas claves no está presente en data, se asigna el valor None.
        username = data.get('username', None)
        email = data.get('email', None)
        # Verificamos si username o email son None. 
        # Si alguno de ellos lo es, significa que faltan datos importantes. 
        # En tal caso, se establece un mensaje de error en response_body, 
        # se añade un diccionario vacío a results, y se retorna una respuesta con el estado 400 Bad Request.
        if not username or not email:
            response_body['message'] = 'Faltan datos'
            response_body['results'] = {}
            return response_body, 400
        #  Preguntamos si alguien tiene un nombre de usuario o un correo electrónico específico. 
        username_exist = db.session.execute(db.select(Users).where(Users.username == username)).scalar()
        email_exist = db.session.execute(db.select(Users).where(Users.email == email)).scalar()
        if username_exist or email_exist:
            response_body['message'] = 'El usuario ya existe'
            response_body['results'] = {}
            return response_body, 404
        # Sino exixte se crea una nueva instancia para Users con los detalles del nuevo usuario.
        row = Users(username = data['username'], 
                    email = data['email'],
                    firstname = data['firstname'],
                    lastname = data['lastname'])
        # añade esta nueva instancia a la sesión de la base de datos y hace un commit para guardar los cambios
        db.session.add(row)
        db.session.commit()
        response_body['message'] = "Usuario agregado"
        response_body['results'] = row.serialize()
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
        # obtengo los datos JSON del request
        data = request.get_json()
        # buscar el usuario por id
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        # cuando lo encuentre, tomamos los datos (data.get()) y actualizando los campos del usuario que hemos encontrado en la base de datos. 
        # Si algún campo no está en los datos de la solicitud, mantenemos el valor actual de ese campo en el usuario.
        user.username = data.get('username', user.username)
        user.email = data.get('email', user.email)
        user.firstname = data.get('firstname', user.firstname)
        user.lastname = data.get('lastname', user.lastname)
        db.session.commit()
        response_body['results'] = user.serialize()
        response_body['message'] = f'Usuario {user_id} actualizado'
        return response_body, 200
    if request.method == 'DELETE':
        # Obtenemos la instancia del usuario a eliminar
        user = db.session.execute(db.select(Users).where(Users.id == user_id)).scalar()
        if not user:
            response_body['results'] = {}
            response_body['message'] = f'No existe el usuario {user_id}'
            return response_body, 404
        # instancia para la eliminación
        db.session.delete(user)
        db.session.commit()
        response_body['message'] = f'Usuario {user_id} eliminado'
        return response_body, 200

@api.route('/ingredient/<int:ingredient_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_ingredient(ingredient_id):
    response_body = {}
    if request.method == 'GET':
        row = db.session.execute(db.select(Ingredient).where(Ingredient.id == ingredient_id)).scalar()
        if not row:
            response_body['results'] = {}
            response_body['message'] = f'Ingredient {ingredient_id} not exist'
            return response_body, 404
        response_body['results'] = row.serialize()
        response_body['message'] = f'Ingredient {ingredient_id} recieved'
        return response_body, 200
    if request.method == 'PUT':
        # obtengo los datos JSON del request
        data = request.get_json()
        # buscar el usuario por id
        ingredient = db.session.execute(db.select(Ingredient).where(Ingredient.id == ingredient_id)).scalar()
        if not ingredient:
            response_body['results'] = {}
            response_body['message'] = f'Ingredient {ingredient_id} not exist'
            return response_body, 404
        # cuando lo encuentre, tomamos los datos (data.get()) y actualizando los campos del usuario que hemos encontrado en la base de datos. 
        # Si algún campo no está en los datos de la solicitud, mantenemos el valor actual de ese campo en el usuario.
        ingredient.name = data.get('name', ingredient.name )
        ingredient.energy = data.get('energy', ingredient.energy)
        ingredient.protein = data.get('firstname', ingredient.protein)
        ingredient.carbohydrates = data.get('carbohydrates', ingredient.carbohydrates)
        ingredient.fat = data.get('fat', ingredient.fat)
        ingredient.sugar = data.get('sugar', ingredient.sugar)
        ingredient.license_object_url = data.get('license_object_url', ingredient.license_object_url)
        db.session.commit()
        response_body['results'] = ingredient.serialize()
        response_body['message'] = f'Ingredient {ingredient_id} updated'
        return response_body, 200
    if request.method == 'DELETE':
        # Obtenemos la instancia del usuario a eliminar
        ingredient = db.session.execute(db.select(Ingredient).where(Ingredient.id == ingredient_id)).scalar()
        if not ingredient:
            response_body['results'] = {}
            response_body['message'] = f'Ingredient {ingredient_id} not exist'
            return response_body, 404
        # instancia para la eliminación
        db.session.delete(ingredient)
        db.session.commit()
        response_body['message'] = f'Ingredient {ingredient_id} deleted'
        return response_body, 200
