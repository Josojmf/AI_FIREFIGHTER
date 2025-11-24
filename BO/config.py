# config.py - BACKOFFICE CON SESIONES SEPARADAS
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 🔥 SECRET KEY ESPECÍFICA PARA BACKOFFICE
    SECRET_KEY = os.getenv('BACKOFFICE_SECRET_KEY', 'firefighter-backoffice-secret-2024')
    
    # API y configuración general
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
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
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin3')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # MFA Configuration
    MFA_ISSUER = os.getenv('MFA_ISSUER', 'FirefighterAI-BackOffice')
    
    @classmethod
    def log_config(cls):
        """Método para debuggear la configuración"""
        print(f"🔒 BackOffice Config:")
        print(f"   - Session cookie: {cls.SESSION_COOKIE_NAME}")
        print(f"   - Secret key: {cls.SECRET_KEY[:20]}...")
        print(f"   - Lifetime: {cls.PERMANENT_SESSION_LIFETIME}s")
        print(f"   - API URL: {cls.API_BASE_URL}")
        print(f"   - Debug: {cls.DEBUG}")
  