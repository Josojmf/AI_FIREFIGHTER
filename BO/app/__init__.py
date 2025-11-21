# app/__init__.py - BACKOFFICE CON SESIONES SEPARADAS
from flask import Flask, request, session
from flask_login import LoginManager, current_user
import logging
from app.config import Config
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
        'SESSION_REFRESH_EACH_REQUEST': Config.SESSION_REFRESH_EACH_REQUEST
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
    def load_user(user_id):
        print(f"🔍 User loader llamado para user_id: {user_id}")
        print(f"📋 Sesión actual: {dict(session)}")
        
        try:
            # ✅ SOLUCIÓN MEJORADA: Buscar usuario en múltiples fuentes
            token = session.get('api_token')
            user_data = session.get('user_data')
            
            print(f"🔑 Token en sesión: {'✅' if token else '❌'}")
            print(f"📦 User data en sesión: {'✅' if user_data else '❌'}")
            
            # PRIMERO: Intentar cargar desde user_data de sesión
            if user_data and user_data.get('id') == user_id:
                print("🔄 Cargando usuario desde session['user_data']")
                user = BackofficeUser.from_dict(user_data)
                if user:
                    print(f"✅ Usuario cargado desde sesión: {user.username}")
                    return user
            
            # SEGUNDO: Intentar cargar desde API con token
            if token:
                print("🔄 Cargando usuario desde API con token")
                user = BackofficeUser.get(user_id, token=token)
                if user:
                    # Actualizar sesión con datos frescos
                    session['user_data'] = user.to_dict()
                    print(f"✅ Usuario cargado desde API: {user.username}")
                    return user
            
            # TERCERO: Fallback a admin local
            if user_id == "admin-local":
                print("🔄 Cargando admin local")
                user = BackofficeUser(
                    id="admin-local",
                    username=Config.ADMIN_USERNAME,
                    email="admin@local",
                    role="admin",
                    mfa_enabled=False,
                    mfa_secret="",
                    token="local-admin-token"
                )
                session['user_data'] = user.to_dict()
                return user
                
            print(f"❌ No se pudo cargar usuario {user_id}")
            return None
                
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

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(memory_cards_bp)

    # Health endpoint simple
    @app.get("/health")
    def health():
        return {"status": "ok", "service": "backoffice"}, 200
    
    # Middleware de debug MEJORADO
    @app.before_request
    def log_request_info():
        if request.endpoint and not request.endpoint.startswith('static'):
            timestamp = datetime.now().strftime("%H:%M:%S")
            session_info = f"Cookie: {request.cookies.get(Config.SESSION_COOKIE_NAME, 'None')[:10]}..."
            print(f"🕒 [{timestamp}] 🌐 [{request.method}] {request.path} - User: {current_user.is_authenticated} | {session_info}")

    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    print(f"🚀 BackOffice iniciado con sesión '{Config.SESSION_COOKIE_NAME}'")
    
    return app