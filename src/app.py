import os
from flask import Flask, jsonify, send_from_directory
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from api.utils import APIException, generate_sitemap
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from api.models import db
from flask_jwt_extended import JWTManager
from datetime import timedelta
from api.seo_routes import seo_bp

# Configuración de entorno
ENV = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../public/')

app = Flask(__name__)
app.url_map.strict_slashes = False

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Configuración de la base de datos
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type=True)
db.init_app(app)

# Configuraciones adicionales
setup_admin(app)
setup_commands(app)

# Registro de Blueprints
app.register_blueprint(api, url_prefix='/api')  # Todas las rutas del backend deben estar bajo /api
app.register_blueprint(seo_bp, url_prefix='/api/seo')

# Configuración de JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Manejo de errores como JSON
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Generar sitemap en modo desarrollo
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

# Redirigir todas las rutas no encontradas a React
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    # Si el archivo existe, servirlo directamente
    if os.path.isfile(os.path.join(static_file_dir, path)):
        return send_from_directory(static_file_dir, path)

    # Excluir rutas de la API del manejo de React
    if path.startswith("api/"):
        return jsonify({"error": "Endpoint not found"}), 404

    # Si no es un archivo estático ni una ruta de API, redirigir al index.html de React
    return send_from_directory(static_file_dir, 'index.html')


# Verificar conexión con la base de datos
@app.route('/db-check', methods=['GET'])
def db_check():
    try:
        result = db.session.execute("SELECT 1").fetchall()
        serializable_result = [dict(row) for row in result]
        return {"message": "Database connection successful", "result": serializable_result}, 200
    except Exception as e:
        app.logger.error(f"Database connection error: {str(e)}")
        return {"error": "Database connection failed", "details": str(e)}, 500

# Endpoint para ejecutar migraciones
@app.route('/run-migrations', methods=['GET'])
def run_migrations():
    try:
        upgrade()  # Aplica las migraciones
        return {"message": "Migrations applied successfully"}, 200
    except Exception as e:
        return {"error": "Failed to apply migrations", "details": str(e)}, 500

# Inicio de la aplicación
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
