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
    
    # Email SendGrid - SIN VALORES HARDCODEADOS
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_SENDER_EMAIL = os.getenv("SENDGRID_SENDER_EMAIL", "onfiretesting@outlook.es")
    SENDGRID_SENDER_NAME = os.getenv("SENDGRID_SENDER_NAME", "FirefighterAI")
    
    # Debug mode
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'


class DevelopmentConfig(Config):
    """Configuración para desarrollo local (Windows/Linux)"""
    
    # URLs locales - usa localhost para desarrollo
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")
    BACKOFFICE_URL = os.getenv("BACKOFFICE_URL", "http://localhost:3001")
    
    # URLs para comunicación interna (si se usa Docker en desarrollo)
    FRONTEND_API_BASE_URL = os.getenv("FRONTEND_API_BASE_URL", "http://localhost:5000")
    BACKOFFICE_API_BASE_URL = os.getenv("BACKOFFICE_API_BASE_URL", "http://localhost:5000")
    PRODUCTION_URL = os.getenv("PRODUCTION_URL", "http://localhost")
    
    # Puertos
    API_PORT = 5000
    FRONTEND_PORT = 8000
    BACKOFFICE_PORT = 3001
    
    # Debug activado
    DEBUG = True
    
    @classmethod
    def print_config(cls):
        print("🏠 CONFIGURACIÓN DE DESARROLLO")
        print("="*60)
        print(f"🌐 API Base URL: {cls.API_BASE_URL}")
        print(f"🖥️  Frontend URL: {cls.FRONTEND_URL}")
        print(f"⚙️  BackOffice URL: {cls.BACKOFFICE_URL}")
        print(f"🔗 Frontend API URL: {cls.FRONTEND_API_BASE_URL}")
        print(f"🔗 BackOffice API URL: {cls.BACKOFFICE_API_BASE_URL}")
        print(f"📧 SendGrid API Key: {cls.SENDGRID_API_KEY[:20]}..." if cls.SENDGRID_API_KEY else "📧 SendGrid API Key: ❌ NO CONFIGURADO")
        print(f"📮 Sender Email: {cls.SENDGRID_SENDER_EMAIL}")
        print(f"🐛 Debug: {cls.DEBUG}")
        print("="*60)


class ProductionConfig(Config):
    """Configuración para producción (Docker en Digital Ocean)"""
    
    # ✅ URLs CORREGIDAS - Detectar automáticamente desde variables de entorno
    # Para comunicación INTERNA entre contenedores Docker
    API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:5000")
    BACKOFFICE_API_BASE_URL = os.getenv("BACKOFFICE_API_BASE_URL", "http://backend:5000")
    
    # Para comunicación EXTERNA desde navegador (IP pública)
    FRONTEND_API_BASE_URL = os.getenv("FRONTEND_API_BASE_URL", "http://167.71.63.108:5000")
    PRODUCTION_URL = os.getenv("PRODUCTION_URL", "http://167.71.63.108")
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://167.71.63.108:8000")
    BACKOFFICE_URL = os.getenv("BACKOFFICE_URL", "http://167.71.63.108:3001")
    
    # Puertos para Docker
    API_PORT = 5000
    FRONTEND_PORT = 8000
    BACKOFFICE_PORT = 3001
    
    # Debug desactivado
    DEBUG = False
    
    @classmethod
    def print_config(cls):
        print("🚀 CONFIGURACIÓN DE PRODUCCIÓN (DOCKER)")
        print("="*60)
        print("📡 URLs INTERNAS (Comunicación Docker):")
        print(f"   API Base URL: {cls.API_BASE_URL}")
        print(f"   BackOffice → API: {cls.BACKOFFICE_API_BASE_URL}")
        print("")
        print("🌍 URLs EXTERNAS (Navegador):")
        print(f"   Production URL: {cls.PRODUCTION_URL}")
        print(f"   Frontend URL: {cls.FRONTEND_URL}")
        print(f"   BackOffice URL: {cls.BACKOFFICE_URL}")
        print(f"   Frontend API URL: {cls.FRONTEND_API_BASE_URL}")
        print("")
        print(f"📧 SendGrid configurado: {'✅' if cls.SENDGRID_API_KEY else '❌'}")
        print(f"🐛 Debug: {cls.DEBUG}")
        print("="*60)


# Mapeo de configuraciones
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
}


def get_config():
    """
    Obtener configuración según el entorno.
    
    Detección automática:
    1. Variable ENVIRONMENT
    2. Presencia de /.dockerenv (contenedor Docker)
    3. Variable DOCKER_ENV
    """
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    # Detectar automáticamente si estamos en Docker/producción
    if os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV', 'false').lower() == 'true':
        env = 'production'
        print("🐳 Entorno Docker detectado - usando configuración de PRODUCCIÓN")
    else:
        print(f"💻 Usando configuración de: {env.upper()}")
    
    config_class = config_map.get(env, DevelopmentConfig)
    config_class.print_config()
    return config_class


# Instancia global de configuración
AppConfig = get_config()


# Para compatibilidad con código existente
API_BASE_URL = AppConfig.API_BASE_URL
FRONTEND_URL = AppConfig.FRONTEND_URL
BACKOFFICE_URL = AppConfig.BACKOFFICE_URL
FRONTEND_API_BASE_URL = AppConfig.FRONTEND_API_BASE_URL
BACKOFFICE_API_BASE_URL = AppConfig.BACKOFFICE_API_BASE_URL
PRODUCTION_URL = AppConfig.PRODUCTION_URL
MONGO_URI = AppConfig.get_mongo_uri()
SECRET_KEY = AppConfig.SECRET_KEY


# Helper functions para obtener URLs según el contexto
def get_api_url_for_server():
    """
    Obtener URL de API para comunicación servidor a servidor.
    En producción Docker: http://backend:5000
    En desarrollo: http://localhost:5000
    """
    return AppConfig.API_BASE_URL


def get_api_url_for_browser():
    """
    Obtener URL de API para comunicación desde navegador (JavaScript).
    En producción: http://167.71.63.108:5000
    En desarrollo: http://localhost:5000
    """
    if AppConfig.ENVIRONMENT == 'production':
        return AppConfig.FRONTEND_API_BASE_URL
    return AppConfig.API_BASE_URL


def is_production():
    """Verificar si estamos en producción"""
    return AppConfig.ENVIRONMENT == 'production'


def is_docker():
    """Verificar si estamos corriendo en Docker"""
    return os.path.exists('/.dockerenv') or os.getenv('DOCKER_ENV', 'false').lower() == 'true'


# Imprimir resumen de configuración al importar
if __name__ == "__main__":
    print("\n" + "="*60)
    print("📋 RESUMEN DE CONFIGURACIÓN")
    print("="*60)
    print(f"Entorno: {AppConfig.ENVIRONMENT}")
    print(f"Docker: {'Sí' if is_docker() else 'No'}")
    print(f"Debug: {'Activado' if AppConfig.DEBUG else 'Desactivado'}")
    print(f"\nAPI URL (servidor): {get_api_url_for_server()}")
    print(f"API URL (navegador): {get_api_url_for_browser()}")
    print(f"Frontend URL: {FRONTEND_URL}")
    print(f"BackOffice URL: {BACKOFFICE_URL}")
    print(f"\nMongoDB URI: {MONGO_URI[:50]}...")
    print("="*60)
