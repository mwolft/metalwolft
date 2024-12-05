import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate, upgrade
from flask_swagger import swagger
from flask_cors import CORS
from api.utils import APIException, generate_sitemap
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from api.models import db
from flask_jwt_extended import JWTManager
from datetime import timedelta
from api.seo_routes import seo_bp  

ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Database configuration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# Other configurations 
setup_admin(app) 
setup_commands(app)
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(seo_bp, url_prefix='/')  

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    # Si el archivo existe, se sirve directamente
    if os.path.isfile(os.path.join(static_file_dir, path)):
        return send_from_directory(static_file_dir, path)

    # Si la ruta es manejada por Flask, no redirigirla a React
    flask_routes = [rule.rule for rule in app.url_map.iter_rules()]
    if f"/{path}" in flask_routes:
        return sitemap()  # Reemplaza con el comportamiento deseado si necesitas algo dinámico

    # Redirige a React para rutas no definidas en Flask
    return send_from_directory(static_file_dir, 'index.html')

# Endpoint to check the database connection
@app.route('/db-check', methods=['GET'])
def db_check():
    try:
        result = db.session.execute("SELECT 1").fetchall()
        serializable_result = [dict(row) for row in result]

        return {"message": "Database connection successful", "result": serializable_result}, 200
    except Exception as e:
        app.logger.error(f"Database connection error: {str(e)}")
        return {"error": "Database connection failed", "details": str(e)}, 500

# Endpoint to run migrations
@app.route('/run-migrations', methods=['GET'])
def run_migrations():
    try:
        upgrade()  # Applies the migrations
        return {"message": "Migrations applied successfully"}, 200
    except Exception as e:
        return {"error": "Failed to apply migrations", "details": str(e)}, 500

# This only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
