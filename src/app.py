import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory, request, current_app, redirect, abort
from flask_migrate import Migrate, upgrade
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_talisman import Talisman
from api.models import Products

from api.utils import APIException, mail
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands
from api.models import db
from api.seo_routes import seo_bp
from api.email_routes import email_bp
from api.password_recovery_endpoints import auth_bp


# 1) Entorno y paths
env = os.getenv("FLASK_ENV", "production")
print(f"⚙️  Flask env: {env}")
static_file_dir = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'build')
)

# 2) Sesión requests con reintentos (para Prerender)
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))

# 3) Creación de la app
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.url_map.strict_slashes = False

# 4) Content Security Policy
talisman_csp = {
    'default-src': ["'self'"],
    'script-src': [
        "'self'",
        "'nonce-1a12a484-04e3-48bb-9ab9-06bbefd67b71'",
        "*.redsys.es",
        "'sha256-nmdWpNZtfW/g70FiD8aVMrYnm6eHHzPr1+Bs1kHTXWA='",
        "'sha256-L/bgcJk7dMrzaGC8frU560Om/mGzl/NWZt9OsuF0fr8='",
        "'unsafe-inline'"
    ],
    'style-src': ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
    'font-src': ["'self'", "https://fonts.gstatic.com"]
}
force_https = env == "production"
Talisman(app, content_security_policy=talisman_csp, force_https=force_https)

# 5) CORS
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"]
)

# 6) Base de datos
db_url = os.getenv("DATABASE_URL")
if db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Migrate(app, db, directory="src/migrations", compare_type=True)
db.init_app(app)

# 7) JWT
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
JWTManager(app)

# 8) Mail
app.config['MAIL_SERVER']       = os.getenv('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT']         = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS']      = os.getenv('MAIL_USE_TLS', 'True').lower() in ['true','1','t']
app.config['MAIL_USE_SSL']      = os.getenv('MAIL_USE_SSL', 'False').lower() in ['true','1','t']
app.config['MAIL_USERNAME']     = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD']     = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
app.config['FRONTEND_URL']      = os.getenv('FRONTEND_URL', 'http://localhost:3000')
app.config['INVOICE_FOLDER']    = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'src', 'assets', 'invoices'
)
mail.init_app(app)

# 9) Admin y comandos CLI
setup_admin(app)
setup_commands(app)

# 10) Blueprints
app.register_blueprint(api,       url_prefix='/api')
app.register_blueprint(seo_bp)
app.register_blueprint(email_bp,  url_prefix='/api/email')
app.register_blueprint(auth_bp,   url_prefix='/api/auth')


# 11) Prerender.io para bots
BOT_USER_AGENTS = [
    "googlebot", "bingbot", "yandex", "baiduspider", "facebookexternalhit",
    "twitterbot", "rogerbot", "linkedinbot", "embedly", "quora link preview",
    "showyoubot", "outbrain", "pinterest", "vkShare", "W3C_Validator"
]
PRERENDER_SERVICE_URL = os.getenv("PRERENDER_SERVICE_URL", "https://service.prerender.io/")
PRERENDER_TOKEN = os.getenv("PRERENDER_TOKEN")

@app.before_request
def prerender_io():
    excluded_paths = [
        '/sitemap.xml',
        '/robots.txt',
        '/favicon.ico',
        '/_debug_build_files',
        '/db-check',
        '/run-migrations'
    ]

    if request.path.startswith('/api/') or request.path.startswith('/static/'):
        return

    if request.path in excluded_paths:
        return

    ua = request.headers.get("User-Agent", "").lower()
    is_bot = any(bot in ua for bot in BOT_USER_AGENTS)
    current_app.logger.info(f"[Prerender] UA={ua!r} is_bot={is_bot} path={request.path}")

    if request.method == "GET" and is_bot:
        target = f"{PRERENDER_SERVICE_URL}https://www.metalwolft.com{request.path}"
        current_app.logger.info(f"[Prerender] Fetching snapshot from {target}")

        try:
            resp = session.get(
                target,
                headers={
                    "X-Prerender-Token": PRERENDER_TOKEN,
                    "User-Agent": ua
                },
                timeout=10  
            )
            current_app.logger.info(f"[Prerender] Got status {resp.status_code}")
            return resp.content, resp.status_code, resp.headers.items()
        except Exception as e:
            current_app.logger.warning(f"[Prerender] ERROR fetching snapshot: {e}")
            return None


# 12) Manejo de errores
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# 13) Servir la SPA React
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_spa(path):
    full_path = os.path.join(static_file_dir, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(static_file_dir, path)
    return send_from_directory(static_file_dir, 'index.html')


# 14) Debug build files
@app.route('/_debug_build_files', methods=['GET'])
def debug_build_files():
    files = []
    for root, dirs, filenames in os.walk(static_file_dir):
        for name in filenames:
            rel = os.path.relpath(os.path.join(root, name), static_file_dir)
            files.append(rel)
    return jsonify(sorted(files))


# 15) Endpoints auxiliares
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
    

@app.route('/sitemap.xml')
def serve_sitemap():
    return send_from_directory(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'static'),
        'sitemap.xml',
        mimetype='application/xml'
    )


redirect_map = {
    "/rejas/rejas-para-ventanas-pittsburgh": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-livingston": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-delhi": "/rejas-para-ventanas",
    "/rejas/rejas-para-ventanas-lancaster": "/rejas-para-ventanas",
    "/puertas-correderas/puerta-corredera-perth": "/puertas-correderas-metalicas",
    "/puertas-correderas/puerta-corredera-adelaida": "/puertas-correderas-metalicas",
    "/puertas-correderas/puerta-corredera-canberra": "/puertas-correderas-metalicas",
    "/puertas-correderas-interiores": "/puertas-correderas-metalicas",
    "/puertas-correderas-exteriores": "/puertas-correderas-metalicas",
    "/puertas-peatonales": "/puertas-peatonales-metalicas",
    "/vallados-metalicos-exteriores": "/vallados-metalicos",
    "/vallados-metalicos/vallado-metalico-geelong": "/vallados-metalicos",
    "/vallados-metalicos": "/vallados-metalicos",
    "/preguntas-frecuentes": "/faq",
}

gone_list = [
    "/blog/instalation-rejas-para-ventanas",
    "/index.php",
    "/blog/medir_hueco_rejas_para_ventanas.php",
    "/blog/medir-hueco-rejas-para-ventanas.php",
    "/blog/instalation-rejas-para-ventanas.php",
    "/rejas-para-ventanas.php",
    "/blog/blog-metal-wolft.php",
    "/",
]

@app.before_request
def handle_legacy_urls():
    if request.path in redirect_map:
        return redirect(redirect_map[request.path], code=301)
    if request.path in gone_list:
        return "Página obsoleta", 410


# 16) Lanzamiento local
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=port, debug=(env == "development"))
