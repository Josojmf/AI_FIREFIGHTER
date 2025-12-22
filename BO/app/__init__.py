"""
Firefighter BackOffice - Application Factory
Versión Ultra Robusta con manejo completo de errores
"""
from flask import Flask, request, session, redirect, jsonify
from flask_login import LoginManager, current_user
from datetime import datetime
import logging
import os
import sys
import traceback
from functools import wraps

from config import Config

def create_app():
    """
    Factory de aplicación Flask con manejo robusto de errores
    """
    try:
        # ============================================
        # 1. CONFIGURACIÓN INICIAL CON FALLBACKS
        # ============================================
        print("🚀 Inicializando Firefighter BackOffice...")
        
        # Crear aplicación con múltiples fallbacks
        try:
            app = Flask(
                __name__, 
                template_folder="templates", 
                static_folder="static",
                static_url_path="/static"
            )
        except Exception as e:
            print(f"❌ Error crítico creando app Flask: {e}")
            # Fallback absoluto
            app = Flask(__name__)
        
        # Configuración con validación
        try:
            app.config.from_object(Config)
            print("✅ Configuración cargada")
        except Exception as e:
            print(f"⚠️  Error cargando configuración: {e}")
            # Configuración de emergencia
            app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'emergency-secret-key')
            app.config['DEBUG'] = True
        
        # ============================================
        # 🔥🔥🔥 AÑADIR ESTA LÍNEA CRÍTICA 🔥🔥🔥
        # ============================================
        # Garantizar que SECRET_KEY esté establecida en app.config para Flask-Session
        app.config['SECRET_KEY'] = Config.SECRET_KEY
        print(f"🔐 Secret Key establecida: {app.config['SECRET_KEY'][:10]}...")
        # ============================================
        
        # ============================================
        # 2. SISTEMA DE SESIONES CON MÚLTIPLES FALLBACKS
        # ============================================
        session_backend = configure_sessions(app)
        
        # ============================================
        # 3. CONFIGURACIÓN DE LOGIN MANAGER
        # ============================================
        login_manager = configure_login_manager(app)
        
        # ============================================
        # 4. CONTEXT PROCESSORS GLOBALES
        # ============================================
        register_context_processors(app)
        
        # ============================================
        # 5. BLUEPRINTS Y RUTAS
        # ============================================
        register_blueprints(app)
        
        # ============================================
        # 6. MANEJADORES GLOBALES DE ERRORES
        # ============================================
        register_error_handlers(app)
        
        # ============================================
        # 7. MIDDLEWARES Y HOOKS
        # ============================================
        register_middlewares(app)
        
        # ============================================
        # 8. RUTAS DEL SISTEMA
        # ============================================
        register_system_routes(app, login_manager)
        
        # ============================================
        # 9. CONFIGURACIÖN FINAL
        # ============================================
        finalize_app_config(app, session_backend)
        
        print("✅ BackOffice inicializado correctamente")
        return app
        
    except Exception as e:
        print(f"💀 ERROR CRÍTICO en create_app: {e}")
        traceback.print_exc()
        
        # Aplicación de emergencia mínima
        emergency_app = Flask(__name__)
        emergency_app.config['SECRET_KEY'] = 'emergency-mode'
        
        @emergency_app.route('/')
        def emergency_root():
            return """
            <h1>⚠️ BackOffice en Modo Emergencia</h1>
            <p>El sistema ha encontrado un error crítico.</p>
            <p>Verifica los logs para más información.</p>
            <p>Error: {}</p>
            """.format(str(e))
        
        @emergency_app.route('/health')
        def emergency_health():
            return {'status': 'emergency', 'error': str(e)}, 503
        
        return emergency_app


def configure_sessions(app):
    """
    Configurar sistema de sesiones con múltiples fallbacks
    """
    print("🔧 Configurando sistema de sesiones...")
    
    session_config = {
        "SECRET_KEY": Config.SECRET_KEY,  # 🔥 CRÍTICO: Debe estar PRIMERO
        "SESSION_COOKIE_NAME": Config.SESSION_COOKIE_NAME,
        "SESSION_COOKIE_PATH": Config.SESSION_COOKIE_PATH,
        "SESSION_COOKIE_HTTPONLY": Config.SESSION_COOKIE_HTTPONLY,
        "SESSION_COOKIE_SECURE": "false",
        "SESSION_COOKIE_SAMESITE": Config.SESSION_COOKIE_SAMESITE,
        "SESSION_COOKIE_DOMAIN": Config.SESSION_COOKIE_DOMAIN,
        "PERMANENT_SESSION_LIFETIME": Config.PERMANENT_SESSION_LIFETIME,
        "SESSION_REFRESH_EACH_REQUEST": Config.SESSION_REFRESH_EACH_REQUEST,
        "MAX_COOKIE_SIZE": 64 * 1024,  # 64KB máximo
    }
    
    session_backend = "native"  # Por defecto
    session_type = "cookie"
    
    # INTENTO 1: Redis Sessions
    if Config.USE_REDIS_SESSIONS:
        try:
            import redis
            from redis import Redis
            
            # Crear cliente Redis con manejo de errores
            redis_client = None
            try:
                redis_client = Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    db=Config.REDIS_DB,
                    password=Config.REDIS_PASSWORD if Config.REDIS_PASSWORD else None,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
                # Test de conexión
                redis_client.ping()
                print("✅ Redis conectado exitosamente")
                
                # Configurar Flask-Session con Redis
                from flask_session import Session
                
                session_config.update({
                    "SESSION_TYPE": "redis",
                    "SESSION_PERMANENT": True,
                    "SESSION_USE_SIGNER": True,
                    "SESSION_KEY_PREFIX": "backoffice:session:",
                    "SESSION_REDIS": redis_client,
                })
                
                app.config.update(session_config)  # 🔥 Aplicar ANTES de Session()
                Session(app)
                session_backend = "flask-session"
                session_type = "redis"
                print("🔧 Sesiones configuradas con Redis")
                
            except Exception as redis_error:
                print(f"⚠️  Redis falló: {redis_error}")
                if redis_client:
                    redis_client.close()
                raise Exception("Redis no disponible")
                
        except ImportError:
            print("⚠️  Redis no disponible, usando fallback")
        except Exception as e:
            print(f"⚠️  Error Redis: {e}")
    
    # INTENTO 2: Filesystem Sessions
    if session_backend == "native":
        try:
            from flask_session import Session
            
            # Crear directorio seguro para sesiones
            session_dir = "/tmp/flask_sessions_backoffice"
            try:
                os.makedirs(session_dir, mode=0o700, exist_ok=True)
                print(f"✅ Directorio de sesiones: {session_dir}")
            except Exception as dir_error:
                print(f"⚠️  Error directorio: {dir_error}")
                session_dir = None
            
            session_config.update({
                "SESSION_TYPE": "filesystem",
                "SESSION_PERMANENT": True,
                "SESSION_USE_SIGNER": True,
                "SESSION_KEY_PREFIX": "backoffice:session:",
                "SESSION_FILE_DIR": session_dir or "/tmp",
                "SESSION_FILE_THRESHOLD": 500,
                "SESSION_FILE_MODE": 0o600,
            })
            
            app.config.update(session_config)  # 🔥 Aplicar ANTES de Session()
            Session(app)
            session_backend = "flask-session"
            session_type = "filesystem"
            print("🔧 Sesiones configuradas con Filesystem")
            
        except ImportError:
            print("⚠️  Flask-Session no disponible, usando sesiones nativas")
        except Exception as e:
            print(f"⚠️  Error Filesystem sessions: {e}")
    
    # INTENTO 3: Sesiones nativas (cookie-based)
    if session_backend == "native":
        print("🔧 Usando sesiones nativas (cookies)")
        print("⚠️  ADVERTENCIA: Sesiones grandes pueden causar problemas")
        session_type = "cookie"
        app.config.update(session_config)  # 🔥 Aplicar config
    
    return {"backend": session_backend, "type": session_type}

def configure_login_manager(app):
    """Configurar Flask-Login con manejo robusto"""
    print("🔧 Configurando Flask-Login...")
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    # Configuración básica
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para acceder a esta página."
    login_manager.login_message_category = "warning"
    login_manager.session_protection = Config.SESSION_PROTECTION
    login_manager.refresh_view = "auth.refresh"
    login_manager.needs_refresh_message = "Tu sesión ha expirado, por favor inicia sesión nuevamente."
    login_manager.needs_refresh_message_category = "warning"
    
    # User loader robusto
    @login_manager.user_loader
    def load_user(user_id):
        """Cargar usuario con múltiples fallbacks"""
        try:
            from app.models.user import BackofficeUser
            from flask import session
            
            # Verificar sesión activa
            if not session:
                print(f"❌ user_loader: No hay sesión (user_id: {user_id})")
                return None
            
            # 1. Buscar en cache de sesión
            user_data = session.get('user_data')
            if user_data:
                try:
                    user = BackofficeUser.from_dict(user_data)
                    print(f"✅ user_loader: Usuario desde sesión: {user.username}")
                    return user
                except Exception as e:
                    print(f"⚠️  user_loader: Error deserializando: {e}")
            
            # 2. Buscar desde API
            api_token = session.get('api_token')
            if api_token:
                try:
                    user = BackofficeUser.get(user_id, api_token)
                    if user:
                        # Cache en sesión
                        session['user_data'] = user.to_dict()
                        session.modified = True
                        print(f"✅ user_loader: Usuario desde API: {user.username}")
                        return user
                except Exception as e:
                    print(f"⚠️  user_loader: Error API: {e}")
            
            # 3. Usuario mínimo de emergencia (solo lectura)
            print(f"⚠️  user_loader: Creando usuario de emergencia para {user_id}")
            return BackofficeUser.emergency_user(user_id)
            
        except Exception as e:
            print(f"💀 user_loader ERROR: {e}")
            traceback.print_exc()
            return None
    
    return login_manager


def register_context_processors(app):
    """Registrar context processors globales"""
    
    @app.context_processor
    def inject_global_vars():
        """Inyectar variables globales en todos los templates"""
        try:
            from config import Config
            
            # Determinar API URL dinámicamente
            def get_api_base_url():
                # Prioridad 1: Variable de entorno explícita
                api_public_url = os.getenv('API_PUBLIC_URL')
                if api_public_url:
                    return api_public_url
                
                # Prioridad 2: Configuración
                if hasattr(Config, 'API_PUBLIC_URL') and Config.API_PUBLIC_URL:
                    return Config.API_PUBLIC_URL
                
                # Prioridad 3: Construir dinámicamente
                hostname = request.host.split(':')[0] if request.host else 'localhost'
                
                if Config.DOCKER:
                    # Docker: usar mismo host, puerto 5000
                    return f"http://{hostname}:5000"
                else:
                    # Desarrollo: localhost
                    return "http://localhost:5000"
            
            # Variables para templates
            return {
                'api_base_url': get_api_base_url(),
                'Config': Config,
                'current_year': datetime.now().year,
                'app_name': 'Firefighter AI BackOffice',
                'app_version': '2.0.0',
                'debug_mode': Config.DEBUG,
            }
            
        except Exception as e:
            print(f"⚠️  Error en context processor: {e}")
            return {'api_base_url': 'http://localhost:5000'}


def register_blueprints(app):
    """Registrar blueprints con manejo de errores"""
    blueprints = [
        ('auth', 'app.routes.auth'),
        ('dashboard', 'app.routes.dashboard'),
        ('users', 'app.routes.users'),
        ('memory_cards', 'app.routes.memory_cards'),
        ('access_tokens', 'app.routes.access_tokens'),
    ]
    
    for name, module_path in blueprints:
        try:
            module = __import__(module_path, fromlist=['bp'])
            if hasattr(module, 'bp'):
                app.register_blueprint(module.bp)
                print(f"✅ Blueprint registrado: {name}")
            else:
                print(f"⚠️  No se encontró bp en {module_path}")
        except Exception as e:
            print(f"❌ Error registrando blueprint {name}: {e}")
            traceback.print_exc()


def register_error_handlers(app):
    """Registrar manejadores globales de errores"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Página no encontrada"""
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Not found', 'message': str(error)}), 404
        
        return """
        <!DOCTYPE html>
        <html>
        <head><title>404 - No encontrado</title></head>
        <body>
            <h1>⚠️ Página no encontrada</h1>
            <p>La página que buscas no existe.</p>
            <p><a href="/">Volver al inicio</a></p>
        </body>
        </html>
        """, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Error interno del servidor"""
        print(f"💀 ERROR 500: {error}")
        traceback.print_exc()
        
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({
                'error': 'Internal server error',
                'message': 'Something went wrong',
                'request_id': getattr(request, 'request_id', 'unknown')
            }), 500
        
        return """
        <!DOCTYPE html>
        <html>
        <head><title>500 - Error interno</title></head>
        <body>
            <h1>⚠️ Error interno del servidor</h1>
            <p>Ha ocurrido un error inesperado. Nuestro equipo ha sido notificado.</p>
            <p><a href="/">Volver al inicio</a></p>
        </body>
        </html>
        """, 500
    
    @app.errorhandler(Exception)
    def handle_all_exceptions(error):
        """Manejar cualquier excepción no capturada"""
        print(f"💀 EXCEPCIÓN NO MANEJADA: {error}")
        traceback.print_exc()
        
        # Log detallado
        error_info = {
            'error': str(error),
            'type': type(error).__name__,
            'path': request.path,
            'method': request.method,
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string,
            'timestamp': datetime.now().isoformat(),
        }
        
        print("📋 Error detallado:", error_info)
        
        return jsonify({
            'error': 'Unhandled exception',
            'message': 'An unexpected error occurred'
        }), 500


def register_middlewares(app):
    """Registrar middlewares y hooks"""
    
    @app.before_request
    def before_request_hook():
        """Hook antes de cada request"""
        try:
            # Generar ID de request
            request.request_id = os.urandom(8).hex()
            
            # Log básico
            if not request.path.startswith('/static'):
                ts = datetime.now().strftime("%H:%M:%S")
                log_msg = f"[{ts}] {request.method} {request.path}"
                
                if current_user.is_authenticated:
                    log_msg += f" | user={current_user.username}"
                
                print(log_msg)
                
                # Debug detallado si está en debug mode
                if Config.DEBUG and request.path.startswith(('/auth', '/dashboard')):
                    print(f"📋 Session keys: {list(session.keys())}")
                    print(f"📋 Headers: {dict(request.headers)}")
                
        except Exception as e:
            print(f"⚠️  Error en before_request: {e}")
    
    @app.after_request
    def after_request_hook(response):
        """Hook después de cada request"""
        try:
            # Headers de seguridad
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Cache control
            if not Config.DEBUG:
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            
            # Request ID para tracking
            if hasattr(request, 'request_id'):
                response.headers['X-Request-ID'] = request.request_id
            
            # CORS para desarrollo
            if Config.DEBUG:
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
        except Exception as e:
            print(f"⚠️  Error en after_request: {e}")
        
        return response


def register_system_routes(app, login_manager):
    """Registrar rutas del sistema"""
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        try:
            # Verificar conexión a Redis si está configurado
            redis_status = 'not_configured'
            if Config.USE_REDIS_SESSIONS:
                try:
                    import redis
                    r = redis.Redis(
                        host=Config.REDIS_HOST,
                        port=Config.REDIS_PORT,
                        socket_connect_timeout=2
                    )
                    r.ping()
                    redis_status = 'connected'
                except:
                    redis_status = 'disconnected'
            
            health_info = {
                'status': 'healthy',
                'service': 'backoffice',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'environment': Config.ENVIRONMENT,
                'redis': redis_status,
                'session_backend': app.config.get('SESSION_TYPE', 'native'),
            }
            
            return jsonify(health_info), 200
            
        except Exception as e:
            return jsonify({
                'status': 'degraded',
                'error': str(e)
            }), 500
    
    @app.route('/')
    def root_redirect():
        """Redirección raíz"""
        try:
            if current_user.is_authenticated:
                return redirect('/dashboard')
            return redirect('/auth/login')
        except:
            return redirect('/auth/login')
    
    # ============================================
    # RUTAS DE DIAGNÓSTICO (solo en debug)
    # ============================================
    if Config.DEBUG:
        @app.route('/debug/session')
        def debug_session():
            """Debug endpoint para sesiones"""
            debug_data = {
                'session_keys': list(session.keys()),
                'session_type': app.config.get('SESSION_TYPE'),
                'user_authenticated': current_user.is_authenticated,
                'user_id': current_user.get_id() if current_user.is_authenticated else None,
                'cookies': dict(request.cookies),
                'headers': {k: v for k, v in request.headers if k.lower() not in ['authorization', 'cookie']},
            }
            return jsonify(debug_data)
        
        @app.route('/debug/config')
        def debug_config():
            """Debug endpoint para configuración"""
            safe_config = {}
            for key in dir(Config):
                if not key.startswith('_'):
                    try:
                        value = getattr(Config, key)
                        # Ocultar valores sensibles
                        if any(sensitive in key.lower() for sensitive in ['secret', 'password', 'key', 'token']):
                            if value:
                                safe_config[key] = f"***{str(value)[-4:]}" if len(str(value)) > 4 else "***"
                            else:
                                safe_config[key] = None
                        else:
                            safe_config[key] = value
                    except:
                        safe_config[key] = 'ERROR'
            return jsonify(safe_config)
    
    # ============================================
    # RUTA DE DIAGNÓSTICO DE SECRET KEY
    # ============================================
    @app.route('/debug/secret')
    def debug_secret():
        """Verificar que SECRET_KEY está configurada"""
        secret_in_config_class = Config.SECRET_KEY
        secret_in_app_config = app.config.get('SECRET_KEY')
        
        debug_info = {
            'config_class_secret': f"{secret_in_config_class[:10]}..." if secret_in_config_class else None,
            'app_config_secret': f"{secret_in_app_config[:10]}..." if secret_in_app_config else None,
            'equal': secret_in_config_class == secret_in_app_config,
            'session_type': app.config.get('SESSION_TYPE'),
            'flask_session_configured': 'flask_session' in sys.modules,
        }
        return jsonify(debug_info)


def finalize_app_config(app, session_backend):
    """Configuración final de la aplicación"""
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Log de inicio
    print("=" * 70)
    print("🚀 FIREFIGHTER BACKOFFICE - INICIALIZACIÓN COMPLETA")
    print("=" * 70)
    print(f"🌍 Environment: {Config.ENVIRONMENT}")
    print(f"🐋 Docker Mode: {Config.DOCKER}")
    print(f"🔧 Session Backend: {session_backend['backend']} ({session_backend['type']})")
    print(f"📊 Log Level: {Config.LOG_LEVEL}")
    print(f"🌐 API URL: {app.config.get('API_BASE_URL', 'Not set')}")
    print(f"🔑 Cookie Name: {Config.SESSION_COOKIE_NAME}")
    print(f"🚪 Login View: {app.login_manager.login_view}")
    print("=" * 70)
    
    # Advertencias importantes
    if Config.ENVIRONMENT == 'production':
        if Config.DEBUG:
            print("⚠️  ADVERTENCIA CRÍTICA: DEBUG ACTIVADO EN PRODUCCIÓN")
        
        if not Config.SESSION_COOKIE_SECURE:
            print("⚠️  ADVERTENCIA: SESSION_COOKIE_SECURE=False en producción")
        
        if Config.ADMIN_PASSWORD == 'admin123':
            print("⚠️  ADVERTENCIA: Contraseña de admin por defecto")
    
    if session_backend['backend'] == 'native':
        print("⚠️  ADVERTENCIA: Sesiones nativas pueden tener limitaciones")
    
    print("✅ Aplicación lista para recibir requests")
    print("=" * 70)