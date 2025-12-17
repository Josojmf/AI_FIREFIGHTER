# app/__init__.py - BACKOFFICE CON FLASK-SESSION Y FALLBACKS COMPLETOS

from flask import Flask, request, session, redirect
from flask_login import LoginManager, current_user
from datetime import datetime
import logging
import os

from config import Config

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)

    # 🔥 CONFIGURACIÓN COMPLETA DE SESIONES CON MÚLTIPLES FALLBACKS
    session_config = {
        # Nombre de la cookie
        "SESSION_COOKIE_NAME": Config.SESSION_COOKIE_NAME,
        "SESSION_COOKIE_PATH": Config.SESSION_COOKIE_PATH,
        "SESSION_COOKIE_HTTPONLY": Config.SESSION_COOKIE_HTTPONLY,
        "SESSION_COOKIE_SECURE": Config.SESSION_COOKIE_SECURE,
        "SESSION_COOKIE_SAMESITE": Config.SESSION_COOKIE_SAMESITE,
        "SESSION_COOKIE_DOMAIN": Config.SESSION_COOKIE_DOMAIN,
        "PERMANENT_SESSION_LIFETIME": Config.PERMANENT_SESSION_LIFETIME,
        "SESSION_REFRESH_EACH_REQUEST": Config.SESSION_REFRESH_EACH_REQUEST,
        
        # IMPORTANTE: Configurar secret key robusta para sesiones firmadas
        "SECRET_KEY": Config.SECRET_KEY,
    }
    
    # 🔄 SISTEMA DE FALLBACKS PARA SESIONES
    session_backend = None
    session_type = "filesystem"  # Por defecto
    
    try:
        # INTENTO 1: Usar Flask-Session con Redis si está configurado
        if Config.USE_REDIS_SESSIONS:
            try:
                import redis
                # Construir URL de Redis
                redis_url = f"redis://"
                if Config.REDIS_PASSWORD:
                    redis_url += f":{Config.REDIS_PASSWORD}@"
                redis_url += f"{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}"
                
                session_config.update({
                    "SESSION_TYPE": "redis",
                    "SESSION_PERMANENT": True,
                    "SESSION_USE_SIGNER": True,
                    "SESSION_KEY_PREFIX": "backoffice_session:",
                    "SESSION_REDIS": redis.from_url(redis_url),
                })
                
                session_type = "redis"
                print("🔧 Configurando sesiones con Redis")
                
                # Verificar conexión a Redis
                try:
                    r = redis.Redis(
                        host=Config.REDIS_HOST,
                        port=Config.REDIS_PORT,
                        db=Config.REDIS_DB,
                        password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                        socket_connect_timeout=2
                    )
                    r.ping()
                    print("✅ Redis conectado para sesiones")
                except Exception as redis_error:
                    print(f"❌ Redis no disponible: {redis_error}")
                    raise Exception("Redis falló")
                    
            except ImportError:
                print("⚠️  Redis no disponible, cambiando a filesystem")
                raise Exception("Redis no disponible")
            except Exception as e:
                print(f"⚠️  Error con Redis: {e}")
                raise Exception(f"Redis error: {e}")
        
        # INTENTO 2: Usar Flask-Session con filesystem
        if session_type != "redis":
            session_config.update({
                "SESSION_TYPE": "filesystem",
                "SESSION_PERMANENT": True,
                "SESSION_USE_SIGNER": True,
                "SESSION_KEY_PREFIX": "backoffice_session:",
                "SESSION_FILE_DIR": "/tmp/flask_sessions",
                "SESSION_FILE_THRESHOLD": 100,
                "SESSION_FILE_MODE": 0o600,
            })
            session_type = "filesystem"
            print("🔧 Configurando sesiones con filesystem")
            
            # Crear directorio de sesiones si no existe
            try:
                os.makedirs("/tmp/flask_sessions", exist_ok=True)
                print("✅ Directorio de sesiones creado")
            except Exception as e:
                print(f"⚠️  Error creando directorio de sesiones: {e}")
        
        # 🔥 INICIALIZAR FLASK-SESSION
        try:
            from flask_session import Session
            Session(app)
            print(f"✅ Flask-Session inicializado ({session_type})")
            session_backend = "flask-session"
        except ImportError:
            print("⚠️  Flask-Session no instalado")
            print("ℹ️  Ejecuta: pip install Flask-Session")
            session_backend = "native"
        except Exception as e:
            print(f"❌ Error inicializando Flask-Session: {e}")
            session_backend = "native"
            
    except Exception as e:
        print(f"⚠️  Error en configuración de sesiones: {e}")
        print("🔄 Usando sesiones nativas de Flask (cookie-based)")
        session_backend = "native"
        session_type = "cookie"
    
    # Aplicar configuración final
    app.config.update(session_config)
    
    # 🔥 CONFIGURACIÓN ADICIONAL PARA SESIONES NATIVAS
    if session_backend == "native":
        print("⚠️  MODO SESIONES NATIVAS: Las sesiones se guardarán en cookies")
        print("⚠️  ADVERTENCIA: Las sesiones grandes pueden causar problemas")
        
        # Configurar tamaño máximo de cookie (64KB es el máximo recomendado)
        app.config['MAX_COOKIE_SIZE'] = 64 * 1024  # 64KB

    Config.log_config()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
    login_manager.session_protection = Config.SESSION_PROTECTION

    from app.models.user import BackofficeUser

    @login_manager.user_loader
    def load_user(user_id: str):
        """Reconstruir usuario desde session['user_data'] o crear uno con datos mínimos."""
        print(f"🔍 user_loader: cookie user_id = {user_id}")
        print(f"📋 Sesión actual en user_loader: keys={list(session.keys())}")  # 🔥 DEBUG
        
        # INTENTO 1: Cargar desde session['user_data']
        user_data = session.get("user_data")
        if user_data:
            print(f"📦 user_loader: user_data encontrado (tipo: {type(user_data)})")
            
            # Normalizar ID
            session_id = str(user_data.get("id", ""))
            cookie_id = str(user_id)
            
            if session_id == cookie_id or not session_id or session_id == "None":
                user = BackofficeUser.from_dict(user_data)
                if user:
                    print(f"✅ user_loader: Usuario cargado = {user.username}")
                    return user
                else:
                    print("❌ user_loader: from_dict devolvió None")
            else:
                print(f"⚠️ user_loader: ID mismatch - session={session_id}, cookie={cookie_id}")
        else:
            print("⚠️ user_loader: No hay user_data en sesión")
            
            # DEBUG: Ver qué hay realmente en la sesión
            if session:
                print(f"🔍 Contenido de sesión:")
                for key in session:
                    value = session[key]
                    if key == 'api_token' and value:
                        print(f"  - {key}: {value[:30]}...")
                    else:
                        print(f"  - {key}: {value}")
        
        # INTENTO 2: Cargar desde session['api_token'] y otros campos individuales
        api_token = session.get('api_token')
        if api_token:
            print(f"🔑 user_loader: api_token encontrado, creando usuario desde token")
            
            # Intentar obtener username de diferentes fuentes
            username = (
                session.get('username') or 
                session.get('pending_username') or 
                'admin'
            )
            
            # Intentar obtener user_id real de diferentes fuentes
            real_user_id = (
                session.get('user_id') or
                session.get('pending_user_id') or
                user_id  # Usar el de la cookie como último recurso
            )
            
            print(f"🆔 user_loader: Construyendo usuario con ID={real_user_id}, username={username}")
            
            user = BackofficeUser(
                id=str(real_user_id),
                username=username,
                email="",
                role="admin",
                mfa_enabled=False,
                token=api_token
            )
            
            print(f"✅ user_loader: Usuario creado desde token = {user.username}")
            return user
        
        # INTENTO 3: Usuario mínimo de emergencia
        print(f"🆘 user_loader: Creando usuario mínimo de emergencia para ID={user_id}")
        
        minimal_user = BackofficeUser(
            id=str(user_id),
            username="admin",
            email="",
            role="admin",
            mfa_enabled=False,
            token=None
        )
        
        print(f"⚠️ user_loader: Usuario mínimo creado (sesión probablemente perdida)")
        return minimal_user

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
            auth_status = current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False
            
            print(
                f"🕒 [{ts}] {request.method} {request.path} | "
                f"auth={auth_status} | cookie={cookie_val[:12]}..."
            )
            
            # DEBUG detallado para rutas críticas
            if request.path.startswith("/auth") or request.path.startswith("/dashboard"):
                print(f"📋 DEBUG Sesión en {request.path}:")
                print(f"  - Keys: {list(session.keys())}")
                print(f"  - Session ID: {session.sid if hasattr(session, 'sid') else 'N/A'}")
                print(f"  - Current user: {current_user}")

    # 🔥 RUTAS DE DIAGNÓSTICO Y REPARACIÓN
    @app.route("/debug/session")
    def debug_session():
        """Endpoint completo para debug de sesión"""
        debug_info = {
            'session_info': {
                'keys': list(session.keys()),
                'session_id': session.sid if hasattr(session, 'sid') else 'N/A',
                'session_type': session_type,
                'session_backend': session_backend,
                'modified': session.modified if hasattr(session, 'modified') else 'N/A',
                'permanent': session.permanent if hasattr(session, 'permanent') else 'N/A',
            },
            'user_info': {
                'authenticated': current_user.is_authenticated if hasattr(current_user, 'is_authenticated') else False,
                'current_user': str(current_user),
                'user_id': current_user.get_id() if current_user.is_authenticated else None,
                'username': getattr(current_user, 'username', None),
            },
            'request_info': {
                'cookies': dict(request.cookies),
                'headers': dict(request.headers),
                'method': request.method,
                'path': request.path,
                'remote_addr': request.remote_addr,
            },
            'config_info': {
                'use_redis_sessions': Config.USE_REDIS_SESSIONS,
                'redis_host': Config.REDIS_HOST,
                'redis_port': Config.REDIS_PORT,
                'session_cookie_name': Config.SESSION_COOKIE_NAME,
                'api_base_url': Config.API_BASE_URL,
            },
            'session_data': {}
        }
        
        # Agregar datos de sesión (con cuidado con tokens)
        for key in session:
            if 'token' in key.lower() and session[key]:
                debug_info['session_data'][key] = f"{session[key][:20]}... [{len(session[key])} chars]"
            else:
                debug_info['session_data'][key] = session[key]
        
        print("=" * 70)
        print("🔍 DEBUG SESSION COMPLETO")
        print("=" * 70)
        
        for category, data in debug_info.items():
            print(f"\n📋 {category.upper()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {data}")
        
        print("=" * 70)
        
        return debug_info

    @app.route("/debug/fix-session", methods=['POST'])
    def fix_session():
        """Intentar reparar la sesión manualmente"""
        try:
            print("🛠️  Intentando reparar sesión...")
            
            # Verificar si hay token pero no user_data
            api_token = session.get('api_token')
            user_id = session.get('user_id')
            
            if api_token and user_id:
                print(f"🔍 Token encontrado para user_id: {user_id}")
                
                # Crear user_data básico
                session['user_data'] = {
                    'id': user_id,
                    'username': session.get('username', 'admin'),
                    'email': '',
                    'role': 'admin',
                    'mfa_enabled': False,
                    'token': api_token
                }
                
                session.modified = True
                print("✅ user_data recreado en sesión")
                
                return {
                    'success': True,
                    'message': 'Sesión reparada',
                    'user_data_created': True
                }
            else:
                print("❌ No hay suficiente información para reparar sesión")
                return {
                    'success': False,
                    'message': 'No hay token o user_id en sesión',
                    'api_token': bool(api_token),
                    'user_id': bool(user_id)
                }
                
        except Exception as e:
            print(f"❌ Error reparando sesión: {e}")
            return {
                'success': False,
                'message': f'Error: {str(e)}'
            }, 500

    @app.route("/debug/clear-session")
    def clear_session():
        """Limpiar completamente la sesión (solo para debug)"""
        session.clear()
        print("🧹 Sesión limpiada manualmente")
        return {'success': True, 'message': 'Sesión limpiada'}

    logging.basicConfig(level=logging.INFO)
    print(f"🚀 BackOffice iniciado con cookie '{Config.SESSION_COOKIE_NAME}'")
    print(f"🔧 Session backend: {session_backend} ({session_type})")
    print(f"🔧 Login manager configurado")
    
    # Mostrar advertencia si estamos en modo nativo
    if session_backend == "native":
        print("⚠️  ADVERTENCIA: Modo sesiones nativas - Las sesiones grandes pueden fallar")
        print("⚠️  Recomendado: Instalar Flask-Session: pip install Flask-Session")

    return app