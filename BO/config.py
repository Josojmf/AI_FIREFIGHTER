# config.py - BACKOFFICE CON SESIONES SEPARADAS - VERSIÓN CORREGIDA PARA DOCKER
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 🔥 SECRET KEY ESPECÍFICA PARA BACKOFFICE
    SECRET_KEY = os.getenv('BACKOFFICE_SECRET_KEY')  # SIN valor por defecto
    
    # 🔥 URLs ABSOLUTAS - SIN VALORES POR DEFECTO
    API_BASE_URL = os.getenv('API_BASE_URL')  # SIN valor por defecto
    BACKOFFICE_API_BASE_URL = os.getenv('BACKOFFICE_API_BASE_URL')  # SIN valor por defecto
    
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    
    # 🔥 CONFIGURACIÓN DE COOKIES ESPECÍFICA PARA BACKOFFICE
    SESSION_COOKIE_NAME = 'backoffice_session'  # Diferente del FrontEnd
    SESSION_COOKIE_PATH = '/'  # Disponible en todas las rutas del BO
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # True en producción HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_DOMAIN = None  # Para localhost
    PERMANENT_SESSION_LIFETIME = 3600 * 8  # 8 horas (más corto que FrontEnd)
    
    # 🔥 CONFIGURACIÓN ADICIONAL DE SEGURIDAD
    SESSION_PROTECTION = 'strong'  # Flask-Login protection level
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Admin credentials (para primer acceso)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # MFA Configuration
    MFA_ISSUER = os.getenv('MFA_ISSUER', 'FirefighterAI-BackOffice')
    
    @classmethod
    def validate_config(cls):
        """Validar que la configuración es correcta"""
        errors = []
        
        # Verificar que las URLs críticas están configuradas
        if not cls.API_BASE_URL:
            errors.append("❌ API_BASE_URL no está configurado")
        if not cls.BACKOFFICE_API_BASE_URL:
            errors.append("❌ BACKOFFICE_API_BASE_URL no está configurado")
        if not cls.SECRET_KEY:
            errors.append("❌ SECRET_KEY no está configurado")
            
        return errors
    
    @classmethod
    def log_config(cls):
        """Método para debuggear la configuración"""
        print(f"🔒 BackOffice Config:")
        print(f"   - Session cookie: {cls.SESSION_COOKIE_NAME}")
        print(f"   - Secret key: {cls.SECRET_KEY[:20]}..." if cls.SECRET_KEY and len(cls.SECRET_KEY) > 20 else "   - Secret key: ❌ NO CONFIGURADO")
        print(f"   - Lifetime: {cls.PERMANENT_SESSION_LIFETIME}s")
        print(f"   - API URL: {cls.API_BASE_URL or '❌ NO CONFIGURADO'}")
        print(f"   - BackOffice API URL: {cls.BACKOFFICE_API_BASE_URL or '❌ NO CONFIGURADO'}")
        print(f"   - Debug: {cls.DEBUG}")
        
        # Validar configuración
        errors = cls.validate_config()
        if errors:
            print("🚨 ERRORES DE CONFIGURACIÓN:")
            for error in errors:
                print(f"   {error}")
            return False
        else:
            print("✅ Configuración validada correctamente")
            return True

# 🔥 INICIALIZACIÓN: Verificar configuración al cargar
if __name__ == "__main__":
    # Solo ejecutar validación completa si se ejecuta directamente
    Config.log_config()
else:
    # En modo importación, solo validar si DEBUG está activado
    if Config.DEBUG:
        Config.log_config()