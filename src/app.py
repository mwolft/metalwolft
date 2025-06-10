import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory, request, current_app, Response
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_talisman import Talisman

from api.utils import APIException, mail
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from api.models import db
from api.seo_routes import seo_bp
from api.email_routes import email_bp
from api.password_recovery_endpoints import auth_bp
from api.sitemap import sitemap_bp, generate_sitemap_file

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 1) Creación de la app
env = "development" if os.getenv("FLASK_DEBUG") == "1" else "production"
app = Flask(__name__)
app.url_map.strict_slashes = False

# Directorios de archivos estáticos y sitemap
basedir = os.path.abspath(os.path.dirname(__file__))
static_file_dir = os.path.join(basedir, '..', 'build')
app.config['SITEMAP_FOLDER'] = static_file_dir

# 2) Extensiones y configuración
# 2.1) Prerender.io requests
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# 2.2) CSP
talisman_csp = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'nonce-1a12a484-04e3-48bb-9ab9-06bbefd67b71'",
        "*.redsys.es",
        "'sha256-nmdWpNZtfW/g70FiD8aVMrYnm6eHHzPr1+Bs1kHTXWA='",
        "'sha256-L/bgcJk7dMrzaGC8frU560Om/mGzl/NWZt9OsuF0fr8='"
    ],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"]
}
Talisman(app, content_security_policy=talisman_csp)

# 2.3) CORS
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"])

# 2.4) Base de datos
db_url = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_DATABASE_URI'] = (db_url.replace("postgres://", "postgresql://")
                                             if db_url else "sqlite:////tmp/test.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Migrate(app, db, directory="src/migrations", compare_type=True)
db.init_app(app)

# 2.5) JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
JWTManager(app)

# 2.6) Mail
app.config.update({
    'MAIL_SERVER': os.getenv('MAIL_SERVER', 'smtp.example.com'),
    'MAIL_PORT': int(os.getenv('MAIL_PORT', 587)),
    'MAIL_USE_TLS': os.getenv('MAIL_USE_TLS', 'True').lower() in ['true','1','t'],
    'MAIL_USE_SSL': os.getenv('MAIL_USE_SSL', 'False').lower() in ['true','1','t'],
    'MAIL_USERNAME': os.getenv('MAIL_USERNAME'),
    'MAIL_PASSWORD': os.getenv('MAIL_PASSWORD'),
    'MAIL_DEFAULT_SENDER': os.getenv('MAIL_DEFAULT_SENDER', os.getenv('MAIL_USERNAME')),
    'FRONTEND_URL': os.getenv('FRONTEND_URL', 'http://localhost:3000'),
    'INVOICE_FOLDER': os.path.join(basedir, 'assets', 'invoices')
})
mail.init_app(app)

# 3) Admin y comandos CLI
setup_admin(app)
setup_commands(app)

# 4) Blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(seo_bp)
app.register_blueprint(email_bp, url_prefix='/api/email')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(sitemap_bp)

# 5) Prerender.io para bots (sin cambios)
BOT_USER_AGENTS = [
    "googlebot", "bingbot", "yandex", "baiduspider", "facebookexternalhit",
    "twitterbot", "rogerbot", "linkedinbot", "embedly", "quora link preview",
    "showyoubot", "outbrain", "pinterest", "slackbot", "vkShare", "W3C_Validator"
]
PRERENDER_SERVICE_URL = os.getenv("PRERENDER_SERVICE_URL", "https://service.prerender.io/")
PRERENDER_TOKEN = os.getenv("PRERENDER_TOKEN")

@app.before_request
def prerender_io():
    ua = request.headers.get("User-Agent", "").lower()
    is_bot = any(bot in ua for bot in BOT_USER_AGENTS)
    
    logger.info(f"[Prerender] UA={ua!r} is_bot={is_bot} path={request.path}")

    if request.path.startswith('/api/') or \
       request.path.startswith('/assets/') or \
       request.path.endswith('.js') or \
       request.path.endswith('.css') or \
       request.path.endswith('.png') or \
       request.path.endswith('.jpg') or \
       request.path.endswith('.jpeg') or \
       request.path.endswith('.gif') or \
       request.path.endswith('.ico') or \
       request.path.endswith('.svg') or \
       request.path.endswith('.xml') or \
       request.path.endswith('.txt'): 

        logger.info(f"[Prerender] Skipping prerender for static/API path: {request.path}")
        return None 

    if request.method == "GET" and is_bot:
        target = f"{PRERENDER_SERVICE_URL}{request.url}"
        logger.info(f"[Prerender] Fetching snapshot from {target}")
        try:
            resp = session.get(
                target,
                headers={"X-Prerender-Token": PRERENDER_TOKEN},
                timeout=30
            )
            logger.info(f"[Prerender] Got status {resp.status_code}")
            return resp.content, resp.status_code, resp.headers.items()
        except Exception as e:
            logger.error(f"[Prerender] ERROR fetching snapshot: {e}")
            return None 

# 6) Ruta para servir sitemap estático
@app.route('/sitemap.xml', methods=['GET'])
def serve_sitemap_file():
    return send_from_directory(app.config['SITEMAP_FOLDER'], 'sitemap.xml', mimetype='application/xml')

# 7) Manejo de errores
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code
app.register_error_handler(APIException, handle_invalid_usage)

# 8) Servir la SPA React
def serve_spa(path=''):
    full_path = os.path.join(static_file_dir, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(static_file_dir, path)
    return send_from_directory(static_file_dir, 'index.html')
app.add_url_rule('/', 'root', serve_spa)
app.add_url_rule('/<path:path>', 'spa', serve_spa)

# 9) Endpoints auxiliares (db-check, run-migrations, etc.)
# 15) Endpoints auxiliares
@app.route('/db-check', methods=['GET'])
def db_check():
    try:
        result = db.session.execute("SELECT 1").fetchall()
        return {"message": "Database connection successful", "result": [dict(row) for row in result]}, 200
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return {"error": "Database connection failed", "details": str(e)}, 500

@app.route('/run-migrations', methods=['GET'])
def run_migrations():
    try:
        upgrade()
        return {"message": "Migrations applied successfully"}, 200
    except Exception as e:
        return {"error": "Failed to apply migrations", "details": str(e)}, 500


# Lanzamiento local y generación de sitemap al iniciar
def main():
    logger.info("Generando sitemap antes de arrancar…")
    with app.app_context():
        generate_sitemap_file(app)
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=(env == 'development'))

if __name__ == '__main__':
    main()
