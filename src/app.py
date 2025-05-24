import os
from flask import Flask, jsonify, send_from_directory, request, current_app
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from api.utils import APIException, generate_sitemap, mail
from api.routes import api
from api.admin import setup_admin, admin_bp
from api.commands import setup_commands
from api.models import db
from flask_jwt_extended import JWTManager
from datetime import timedelta
from api.seo_routes import seo_bp
from api.email_routes import email_bp
from api.password_recovery_endpoints import auth_bp
import requests
from flask_talisman import Talisman


# Configuración de la aplicación
env = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'build')

app = Flask(__name__)
app.url_map.strict_slashes = False

# Política de Content Security Policy
talisman_csp = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'nonce-1a12a484-04e3-48bb-9ab9-06bbefd67b71'",
        "*.redsys.es",
        "'sha256-nmdWpNZtfW/g70FiD8aVMrYnm6eHHzPr1+Bs1kHTXWA='",
        "'sha256-L/bgcJk7dMrzaGC8frU560Om/mGzl/NWZt9OsuF0fr8='"
    ],
    'style-src': [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com"
    ],
    'font-src': [
        "'self'",
        "https://fonts.gstatic.com"
    ]
}
Talisman(app, content_security_policy=talisman_csp)

# Configuración de CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"])

# Configuración de la base de datos
db_url = os.getenv("DATABASE_URL")
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, directory="src/migrations", compare_type=True)
db.init_app(app)

# Configuración de JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# Configuración de Mail
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true', '1', 't']
app.config['MAIL_USE_SSL'] = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
app.config['FRONTEND_URL'] = os.getenv('FRONTEND_URL', 'http://localhost:3000')
app.config['INVOICE_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'assets', 'invoices')

mail.init_app(app)

# Configuración adicional
setup_admin(app)
setup_commands(app)

# Registro de Blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(seo_bp)
app.register_blueprint(email_bp, url_prefix='/api/email')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Integración de Prerender.io
BOT_USER_AGENTS = [
    "googlebot", "bingbot", "yandex", "baiduspider", "facebookexternalhit",
    "twitterbot", "rogerbot", "linkedinbot", "embedly", "quora link preview",
    "showyoubot", "outbrain", "pinterest", "slackbot", "vkShare", "W3C_Validator"
]
PRERENDER_SERVICE_URL = os.getenv("PRERENDER_SERVICE_URL", "https://service.prerender.io/")
PRERENDER_TOKEN       = os.getenv("PRERENDER_TOKEN")

@app.before_request
def prerender_io():
    ua     = request.headers.get("User-Agent", "").lower()
    accept = request.headers.get("Accept", "").lower()
    is_bot  = any(bot in ua for bot in BOT_USER_AGENTS)
    is_html = "text/html" in accept

    # --- LOGGING ---
    current_app.logger.info(f"[Prerender] UA={ua!r}  is_bot={is_bot}  is_html={is_html}  path={request.path}")
    # -------------

    if request.method == "GET" and is_bot and is_html:
        target = f"{PRERENDER_SERVICE_URL}{request.url}"
        current_app.logger.info(f"[Prerender] Fetching snapshot from {target}")
        try:
            resp = requests.get(target, headers={"X-Prerender-Token": PRERENDER_TOKEN}, timeout=10)
            current_app.logger.info(f"[Prerender] Got status {resp.status_code}")
            return resp.content, resp.status_code, resp.headers.items()
        except Exception as e:
            current_app.logger.error(f"[Prerender] ERROR fetching snapshot: {e}")


# Manejo de errores personalizados
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# Rutas principales
@app.route('/')
def sitemap():
    if env == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if os.path.isfile(os.path.join(static_file_dir, path)):
        return send_from_directory(static_file_dir, path)
    if path.startswith("api/"):
        return jsonify({"error": "Endpoint not found"}), 404
    return send_from_directory(static_file_dir, 'index.html')

@app.route('/db-check', methods=['GET'])
def db_check():
    try:
        result = db.session.execute("SELECT 1").fetchall()
        return {"message": "Database connection successful", "result": [dict(row) for row in result]}, 200
    except Exception as e:
        current_app.logger.error(f"Database connection error: {e}")
        return {"error": "Database connection failed", "details": str(e)}, 500

@app.route('/run-migrations', methods=['GET'])
def run_migrations():
    try:
        upgrade()
        return {"message": "Migrations applied successfully"}, 200
    except Exception as e:
        return {"error": "Failed to apply migrations", "details": str(e)}, 500

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=(env == "development"))
