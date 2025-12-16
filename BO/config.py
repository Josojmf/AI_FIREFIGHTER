import os
from dotenv import load_dotenv

# 🔥 Cargar variables de entorno desde .env si existe
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)


class Config:
    # =========================================================
    # 🌍 ENTORNO
    # =========================================================
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DOCKER = os.getenv('DOCKER', 'false').lower() in ('true', '1', 't')
    DEBUG = os.getenv('DEBUG', 'false').lower() in ('true', '1', 't')

    # =========================================================
    # 🔐 SEGURIDAD
    # =========================================================
    SECRET_KEY = os.getenv(
        'BACKOFFICE_SECRET_KEY',
        'firefighter-backoffice-secret-key-2024'
    )

    SESSION_COOKIE_NAME = 'backoffice_session'
    SESSION_COOKIE_PATH = '/'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = ENVIRONMENT == 'production'
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = None
    PERMANENT_SESSION_LIFETIME = 3600 * 8  # 8 horas

    SESSION_PROTECTION = 'strong'
    SESSION_REFRESH_EACH_REQUEST = True

    # =========================================================
    # 👤 ADMIN / MFA
    # =========================================================
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    MFA_ISSUER = os.getenv('MFA_ISSUER', 'FirefighterAI-BackOffice')

    # =========================================================
    # 🌐 API CONFIGURATION (CLAVE)
    # =========================================================
    # ⚠️ El Backoffice NO decide la URL
    # ⚠️ Debe venir SIEMPRE por variable de entorno
    API_BASE_URL = os.getenv('API_BASE_URL')

    BACKOFFICE_API_BASE_URL = API_BASE_URL

    # =========================================================
    # 🔴 REDIS
    # =========================================================
    REDIS_HOST = os.getenv('REDIS_HOST', 'redis' if DOCKER else 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))

    # =========================================================
    # ✅ VALIDACIÓN
    # =========================================================
    @classmethod
    def validate_config(cls):
        errors = []

        if not cls.API_BASE_URL:
            errors.append("❌ API_BASE_URL no está configurado (obligatorio)")

        if not cls.SECRET_KEY:
            errors.append("❌ SECRET_KEY no está configurado")

        return errors

    # =========================================================
    # 🪵 LOGGING
    # =========================================================
    @classmethod
    def log_config(cls):
        print("=" * 70)
        print("🔧 BACKOFFICE CONFIGURATION")
        print("=" * 70)
        print(f"🌍 Environment     : {cls.ENVIRONMENT}")
        print(f"📦 Docker Mode    : {cls.DOCKER}")
        print(f"🐛 Debug          : {cls.DEBUG}")
        print(f"🌐 API URL        : {cls.API_BASE_URL}")
        print(f"📡 Redis          : {cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}")
        print(f"🔒 Session Cookie : {cls.SESSION_COOKIE_NAME}")
        print(
            f"🔑 Secret Key     : {cls.SECRET_KEY[:20]}..."
            if cls.SECRET_KEY else "❌ NO SET"
        )
        print(
            f"⏱️  Session Time  : {cls.PERMANENT_SESSION_LIFETIME}s "
            f"({cls.PERMANENT_SESSION_LIFETIME // 3600}h)"
        )
        print("=" * 70)

        errors = cls.validate_config()
        if errors:
            print("🚨 CONFIGURATION ERRORS:")
            for error in errors:
                print(f"   {error}")
            print("=" * 70)
            return False

        print("✅ Configuration validated successfully")
        print("=" * 70)
        return True


# 🔥 Mostrar siempre configuración al arrancar
Config.log_config()
