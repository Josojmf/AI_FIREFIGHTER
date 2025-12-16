# app/__init__.py - BACKOFFICE CON SESIONES SEPARADAS
from flask import Flask, request, session, redirect
from flask_login import LoginManager, current_user
import logging
from config import Config
from datetime import datetime


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # 🔥 CONFIGURACIÓN PRIMERO - CON SECRET_KEY CONSISTENTE
    app.config.from_object(Config)

    # 🔥 CONFIGURACIÓN COMPLETA DE SESIÓN USANDO Config
    app.config.update({
        'SESSION_COOKIE_NAME': Config.SESSION_COOKIE_NAME,
        'SESSION_COOKIE_PATH': Config.SESSION_COOKIE_PATH,
        'SESSION_COOKIE_HTTPONLY': Config.SESSION_COOKIE_HTTPONLY,
        'SESSION_COOKIE_SECURE': Config.SESSION_COOKIE_SECURE,
        'SESSION_COOKIE_SAMESITE': Config.SESSION_COOKIE_SAMESITE,
        'SESSION_COOKIE_DOMAIN': Config.SESSION_COOKIE_DOMAIN,
        'PERMANENT_SESSION_LIFETIME': Config.PERMANENT_SESSION_LIFETIME,
        'SESSION_REFRESH_EACH_REQUEST': Config.SESSION_REFRESH_EACH_REQUEST,
    })

    # Logging de configuración para debug
    Config.log_config()

    # Flask-Login con configuración mejorada
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.session_protection = Config.SESSION_PROTECTION

    from app.models.user import BackofficeUser

    @login_manager.user_loader
    def load_user(user_id: str):
        print(f"🔍 User loader llamado para user_id: {user_id}")

        # 🔥 VALIDACIÓN: Rechazar IDs ficticios inmediatamente
        if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
            print(f"❌ ID ficticio en user_loader: {user_id}")
            return None

        try:
            token = session.get('api_token')
            user_data = session.get('user_data')

            print(f"🔑 Token en sesión: {'✅' if token else '❌'}")
            print(f"📦 User data en sesión: {'✅' if user_data else '❌'}")

            # Si no hay datos suficientes en sesión, no se puede cargar usuario
            if not token or not user_data:
                print(f"❌ No hay datos suficientes en sesión para {user_id}")
                return None

            # Validar que el ID guardado coincide con el user_id
            if user_data.get('id') != user_id:
                print(f"❌ Mismatch de IDs: session={user_data.get('id')} loader={user_id}")
                return None

            # Reconstruir usuario solo desde los datos de sesión
            user = BackofficeUser.from_dict({
                "id": user_id,
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "role": user_data.get("role"),
                "mfa_enabled": user_data.get("mfa_enabled", False),
                "token": token,
            })

            if user:
                print(f"✅ Usuario cargado desde sesión en user_loader: {user.username}")
            else:
                print("❌ BackofficeUser.from_dict devolvió None")

            return user

        except Exception as e:
            print(f"⚠️ Error crítico en user_loader: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Registrar blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.users import bp as users_bp
    from app.routes.memory_cards import bp as memory_cards_bp
    from app.routes.access_tokens import bp as access_tokens_bp  # ← NUEVA LÍNEA

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(memory_cards_bp)
    app.register_blueprint(access_tokens_bp)  # ← NUEVA LÍNEA

    # Health endpoint simple
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "backoffice"}, 200

    # 🔥 NUEVA RUTA: Redirigir raíz al dashboard
    @app.route('/')
    def root_redirect():
        """Redirigir raíz al dashboard"""
        print("🔄 Redirigiendo / → /dashboard")
        return redirect('/dashboard')

    # Middleware de debug MEJORADO
    @app.before_request
    def log_request_info():
        if request.endpoint and not request.endpoint.startswith('static'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            session_info = f"Cookie: {request.cookies.get(Config.SESSION_COOKIE_NAME, 'None')[:10]}..."
            print(
                f"🕒 [{timestamp}] 🌐 [{request.method}] {request.path} - "
                f"User: {current_user.is_authenticated} | {session_info}"
            )

    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    print(f"🚀 BackOffice iniciado con sesión '{Config.SESSION_COOKIE_NAME}'")

    return app
