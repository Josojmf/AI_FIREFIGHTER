# app/__init__.py (VERSIÓN CORREGIDA)
from flask import Flask, request
from flask_login import LoginManager, current_user
import logging
from app.config import Config
from datetime import datetime

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    
    # Configuración PRIMERO
    app.config.from_object(Config)
    
    # Configuración de sesión
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600

    # Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.session_protection = "basic"

    from app.models.user import BackofficeUser

    @login_manager.user_loader
    def load_user(user_id):
        print(f"🔍 User loader llamado para user_id: {user_id}")
        try:
            user = BackofficeUser.get(user_id)
            if user:
                print(f"✅ Usuario cargado: {user.username}")
            return user
        except Exception as e:
            print(f"❌ Error en user_loader: {e}")
            return None

    # Registrar blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.users import bp as users_bp
    from app.routes.memory_cards import bp as memory_cards_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(memory_cards_bp)

    # Health endpoint simple
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "backoffice"}, 200
    
    # Middleware de debug MEJORADO (sin current_user en before_request)
    @app.before_request
    def log_request_info():
        if request.endpoint and not request.endpoint.startswith('static'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            # Evitar acceso a current_user que puede causar reinicios
            print(f"🕒 [{timestamp}] 🔍 [{request.method}] {request.path}")

    # Configurar logging
    logging.basicConfig(level=logging.INFO)  # Cambiar a INFO para menos ruido
    
    return app