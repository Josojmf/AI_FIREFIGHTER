# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SECRET_KEY es CRÍTICA - debe ser la misma siempre
    SECRET_KEY = os.getenv('BACKOFFICE_SECRET_KEY', 'dev-secret-key-para-debugging-12345')
    
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Credenciales de admin local
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # MongoDB
    MONGO_USER = os.getenv('MONGO_USER', 'joso')
    MONGO_PASS = os.getenv('MONGO_PASS', '')
    MONGO_CLUSTER = os.getenv('MONGO_CLUSTER', '')
    DB_NAME = os.getenv('DB_NAME', 'FIREFIGHTER')