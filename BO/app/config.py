# app/config.py - Configuración corregida y unificada
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SECRET_KEY crítica - debe ser consistente
    SECRET_KEY = os.getenv('BACKOFFICE_SECRET_KEY', 'dev-secret-key-para-debugging-12345')
    
    # API URL corregida - SIN /api al final
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    
    # Debug mode
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't', 'yes')
    
    # Credenciales de admin local (fallback)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # MongoDB - Configuración completa
    MONGO_USER = os.getenv('MONGO_USER', 'joso')
    MONGO_PASS = os.getenv('MONGO_PASS', 'XyGItdDKpWkfJfjT')
    MONGO_CLUSTER = os.getenv('MONGO_CLUSTER', 'cluster0.yzzh9ig.mongodb.net')
    DB_NAME = os.getenv('DB_NAME', 'FIREFIGHTER')
    
    # URI completa de MongoDB
    @property
    def MONGO_URI(self):
        return f"mongodb+srv://{self.MONGO_USER}:{self.MONGO_PASS}@{self.MONGO_CLUSTER}/{self.DB_NAME}?retryWrites=true&w=majority"
    
    # Configuración de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # True en producción
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hora
    
    def __repr__(self):
        return f"<Config API_BASE_URL={self.API_BASE_URL} DEBUG={self.DEBUG}>"