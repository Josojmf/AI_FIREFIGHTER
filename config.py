# config.py - Sistema de configuración unificado para desarrollo y producción
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

class Config:
    """Configuración base con valores por defecto"""
    
    # Detectar entorno automáticamente
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    # Base de datos MongoDB
    MONGO_USER = os.getenv("MONGO_USER", "joso")
    MONGO_PASS = os.getenv("MONGO_PASS", "XyGItdDKpWkfJfjT") 
    MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.yzzh9ig.mongodb.net")
    DB_NAME = os.getenv("DB_NAME", "FIREFIGHTER")
    
    # Construir URI de MongoDB
    @classmethod
    def get_mongo_uri(cls):
        if cls.MONGO_USER and cls.MONGO_PASS:
            return f"mongodb+srv://{cls.MONGO_USER}:{cls.MONGO_PASS}@{cls.MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=FirefighterAPI"
        return "mongodb://localhost:27017"
    
    # Seguridad JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "firefighter-secret-key-2024")
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
    
    # Email SendGrid
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_SENDER_EMAIL = os.getenv("SENDGRID_SENDER_EMAIL", "onfiretesting@outlook.es")
    SENDGRID_SENDER_NAME = os.getenv("SENDGRID_SENDER_NAME", "FirefighterAI")
    
    # Debug mode
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'


class DevelopmentConfig(Config):
    """Configuración para desarrollo local"""
    
    # URLs locales
    API_BASE_URL = "http://127.0.0.1:5000"
    FRONTEND_URL = "http://localhost:8000"
    BACKOFFICE_URL = "http://localhost:8080"
    
    # Puertos
    API_PORT = 5000
    FRONTEND_PORT = 8000
    BACKOFFICE_PORT = 8080
    
    # Debug activado
    DEBUG = True
    
    @classmethod
    def print_config(cls):
        print("🏠 CONFIGURACIÓN DE DESARROLLO")
        print("="*50)
        print(f"🌐 API URL: {cls.API_BASE_URL}")
        print(f"🖥️  Frontend URL: {cls.FRONTEND_URL}")
        print(f"⚙️  BackOffice URL: {cls.BACKOFFICE_URL}")
        print(f"📧 SendGrid API Key: {cls.SENDGRID_API_KEY[:20]}...")
        print(f"📮 Sender Email: {cls.SENDGRID_SENDER_EMAIL}")
        print("="*50)


class ProductionConfig(Config):
    """Configuración para producción"""
    
    # URLs de producción
    API_BASE_URL = "http://167.71.63.108:5000"
    FRONTEND_URL = "http://167.71.63.108:8000"
    BACKOFFICE_URL = "http://167.71.63.108:8080"
    
    # Puertos para Docker
    API_PORT = 5000
    FRONTEND_PORT = 8000
    BACKOFFICE_PORT = 3001  # BackOffice usa puerto diferente en producción
    
    # Debug desactivado
    DEBUG = False
    
    @classmethod
    def print_config(cls):
        print("🚀 CONFIGURACIÓN DE PRODUCCIÓN")
        print("="*50)
        print(f"🌐 API URL: {cls.API_BASE_URL}")
        print(f"🖥️  Frontend URL: {cls.FRONTEND_URL}")
        print(f"⚙️  BackOffice URL: {cls.BACKOFFICE_URL}")
        print(f"📧 SendGrid configurado: {'✅' if cls.SENDGRID_API_KEY else '❌'}")
        print("="*50)


# Mapeo de configuraciones
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
}

def get_config():
    """Obtener configuración según el entorno"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    # Detectar automáticamente si estamos en Docker/producción
    if os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV'):
        env = 'production'
    
    config_class = config_map.get(env, DevelopmentConfig)
    config_class.print_config()
    return config_class

# Instancia global de configuración
AppConfig = get_config()

# Para compatibilidad con código existente
API_BASE_URL = AppConfig.API_BASE_URL
FRONTEND_URL = AppConfig.FRONTEND_URL
MONGO_URI = AppConfig.get_mongo_uri()
SECRET_KEY = AppConfig.SECRET_KEY