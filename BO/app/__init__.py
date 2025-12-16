# app/__init__.py - BACKOFFICE

from flask import Flask, request, session, redirect
from flask_login import LoginManager, current_user
from datetime import datetime
import logging

from config import Config


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # Config de sesión explícita
    app.config.update({
        "SESSION_COOKIE_NAME": Config.SESSION_COOKIE_NAME,
        "SESSION_COOKIE_PATH": Config.SESSION_COOKIE_PATH,
        "SESSION_COOKIE_HTTPONLY": Config.SESSION_COOKIE_HTTPONLY,
        "SESSION_COOKIE_SECURE": Config.SESSION_COOKIE_SECURE,
        "SESSION_COOKIE_SAMESITE": Config.SESSION_COOKIE_SAMESITE,
        "SESSION_COOKIE_DOMAIN": Config.SESSION_COOKIE_DOMAIN,
        "PERMANENT_SESSION_LIFETIME": Config.PERMANENT_SESSION_LIFETIME,
        "SESSION_REFRESH_EACH_REQUEST": Config.SESSION_REFRESH_EACH_REQUEST,
    })

    Config.log_config()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
    login_manager.session_protection = Config.SESSION_PROTECTION

    from app.models.user import BackofficeUser

    @login_manager.user_loader
    def load_user(user_id: str):
        """Reconstruir usuario desde session['user_data'] (lo que guarda auth.py)."""
        print(f"🔍 user_loader: cookie user_id = {user_id}")

        user_data = session.get("user_data")
        if not user_data:
            print("❌ user_loader: no hay user_data en sesión")
            return None

        session_id = str(user_data.get("id"))
        if session_id != str(user_id):
            print(f"❌ user_loader: mismatch IDs session={session_id} cookie={user_id}")
            return None

        user = BackofficeUser.from_dict(user_data)
        if user:
            print(f"✅ user_loader: usuario = {user.username}")
        else:
            print("❌ user_loader: from_dict devolvió None")
        return user

    # Blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.users import bp as users_bp
    from app.routes.memory_cards import bp as memory_cards_bp
    from app.routes.access_tokens import bp as access_tokens_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(memory_cards_bp)
    app.register_blueprint(access_tokens_bp)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "backoffice"}, 200

    @app.route("/")
    def root_redirect():
        print("🔄 / -> /dashboard")
        return redirect("/dashboard")

    @app.before_request
    def log_request_info():
        if request.endpoint and not request.endpoint.startswith("static"):
            ts = datetime.now().strftime("%H:%M:%S")
            cookie_val = request.cookies.get(Config.SESSION_COOKIE_NAME, "None")
            print(
                f"🕒 [{ts}] {request.method} {request.path} | "
                f"auth={current_user.is_authenticated} | cookie={cookie_val[:12]}..."
            )

    logging.basicConfig(level=logging.INFO)
    print(f"🚀 BackOffice iniciado con cookie '{Config.SESSION_COOKIE_NAME}'")

    return app
