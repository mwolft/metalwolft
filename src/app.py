import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from api.utils import APIException, generate_sitemap
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from api.models import db
from flask_jwt_extended import JWTManager
from datetime import timedelta
from api.seo_routes import seo_bp  # Importamos el nuevo Blueprint de SEO

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
app.register_blueprint(seo_bp, url_prefix='/')  # Registramos el Blueprint de SEO

# Setup the Flask-JWT-Extended extension
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/routes')
def show_routes():
    output = []
    for rule in app.url_map.iter_rules():
        output.append(str(rule))
    return jsonify(routes=output)

# Generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# Any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0  # Avoid cache memory
    return response

# This only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)