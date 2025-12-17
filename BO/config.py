import os
from dotenv import load_dotenv

# 🔥 Cargar variables de entorno desde .env si existe
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)


class Config:
    # =========================================================
    # 🌍 ENTORNO
    # =========================================================
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    DOCKER = os.getenv("DOCKER", "true").lower() in ("true", "1", "t")  # True para Docker
    DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    # =========================================================
    # 🔐 SEGURIDAD
    # =========================================================
    SECRET_KEY = os.getenv(
        "BACKOFFICE_SECRET_KEY",
        "firefighter-backoffice-secret-key-2024-production"
    )
    
    # 🔐 JWT PARA COMUNICACIÓN CON BACKEND API (NUEVO - CORRECCIÓN DEL ERROR)
    JWT_SECRET = os.getenv(
        "JWT_SECRET",  # Mismo que usa el backend API
        "firefighter-super-secret-jwt-key-2024"  # Default del API config.py
    )
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

    SESSION_COOKIE_NAME = "backoffice_session"
    SESSION_COOKIE_PATH = "/"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = ENVIRONMENT == "production"  # True en producción
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_DOMAIN = os.getenv("SESSION_COOKIE_DOMAIN", None)

    PERMANENT_SESSION_LIFETIME = 3600 * 8  # 8 horas
    SESSION_PROTECTION = "strong"
    SESSION_REFRESH_EACH_REQUEST = True

    # =========================================================
    # 👤 ADMIN / MFA
    # =========================================================
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", os.getenv("ADMIN_PASSWORD_HASH", "admin123"))
    MFA_ISSUER = os.getenv("MFA_ISSUER", "FirefighterAI-BackOffice")

    # =========================================================
    # 🌐 API CONFIGURATION - CRÍTICO PARA DOCKER/SWARM
    # =========================================================
    # En Docker: usa "backend" (nombre del servicio)
    # En local: usa "localhost"
    # En Swarm: usa el nombre del servicio o load balancer
    API_BASE_URL = os.getenv("API_BASE_URL", 
        "http://backend:5000" if DOCKER else "http://localhost:5000"
    )

    # =========================================================
    # 🔴 REDIS (para sesiones en producción)
    # =========================================================
    REDIS_HOST = os.getenv("REDIS_HOST", "redis" if DOCKER else "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    
    # Usar Redis para sesiones en producción
    USE_REDIS_SESSIONS = os.getenv("USE_REDIS_SESSIONS", "true").lower() == "true"

    # =========================================================
    # 📊 MONITORING & LOGGING
    # =========================================================
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SENTRY_DSN = os.getenv("SENTRY_DSN", None)
    
    # CORS para Swarm/Load Balancer
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # =========================================================
    # ✅ VALIDACIÓN
    # =========================================================
    @classmethod
    def validate_config(cls):
        errors = []
        
        if not cls.API_BASE_URL:
            errors.append("❌ API_BASE_URL no está configurado")
        
        # Validar JWT_SECRET (NUEVO)
        if not cls.JWT_SECRET:
            errors.append("❌ JWT_SECRET no está configurado")
        elif cls.JWT_SECRET == "firefighter-super-secret-jwt-key-2024" and cls.ENVIRONMENT == "production":
            errors.append("⚠️  JWT_SECRET es el valor por defecto en producción")
        
        if cls.ENVIRONMENT == "production":
            if not cls.SECRET_KEY or "dev" in cls.SECRET_KEY:
                errors.append("❌ SECRET_KEY inseguro en producción")
            
            if not cls.ADMIN_PASSWORD or cls.ADMIN_PASSWORD == "admin123":
                errors.append("❌ Contraseña de admin por defecto en producción")
        
        return errors

    # =========================================================
    # 🪵 LOGGING MEJORADO
    # =========================================================
    @classmethod
    def log_config(cls):
        import socket
        
        print("=" * 70)
        print("🚀 FIREFIGHTER BACKOFFICE - CONFIGURACIÓN")
        print("=" * 70)
        print(f"🌍 Environment     : {cls.ENVIRONMENT}")
        print(f"🐋 Docker Mode     : {cls.DOCKER}")
        print(f"🐛 Debug           : {cls.DEBUG}")
        print(f"🌐 API URL         : {cls.API_BASE_URL}")
        print(f"🔒 Secure Cookies  : {cls.SESSION_COOKIE_SECURE}")
        print(f"🔑 JWT Secret      : {'✅ Configurado' if cls.JWT_SECRET else '❌ No configurado'}")
        print(f"📡 Redis Sessions  : {cls.USE_REDIS_SESSIONS}")
        print(f"📊 Log Level       : {cls.LOG_LEVEL}")
        
        # Resolver hostname para debug
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            print(f"🖥️  Hostname        : {hostname} ({ip})")
        except:
            pass
        
        # Info de API (sin exponer credenciales)
        if cls.SECRET_KEY:
            secret_preview = cls.SECRET_KEY[:15] + "..." if len(cls.SECRET_KEY) > 15 else cls.SECRET_KEY
            print(f"🔑 Secret Key      : {secret_preview}")
        
        # Info JWT (ocultar valor completo)
        if cls.JWT_SECRET:
            jwt_preview = cls.JWT_SECRET[:10] + "..." if len(cls.JWT_SECRET) > 10 else cls.JWT_SECRET
            print(f"🔐 JWT Preview     : {jwt_preview}")
        
        print("=" * 70)

        errors = cls.validate_config()
        if errors:
            print("🚨 ERRORES DE CONFIGURACIÓN:")
            for e in errors:
                print(f"   {e}")
            
            # En producción, salir si hay errores críticos
            if cls.ENVIRONMENT == "production":
                print("💀 ERRORES CRÍTICOS EN PRODUCCIÓN - ABORTANDO")
                import sys
                sys.exit(1)
            
            print("=" * 70)
            return False

        print("✅ Configuración validada exitosamente")
        print("=" * 70)
        return True


# Mostrar config al arrancar
Config.log_config()