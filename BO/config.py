import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('BACKOFFICE_SECRET_KEY', 'dev-backoffice-secret')
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Admin credentials (para primer acceso)
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')