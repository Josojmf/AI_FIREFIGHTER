from flask_login import UserMixin
import requests
from config import Config

class BackofficeUser(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role
    
    @staticmethod
    def authenticate(username, password):
        # Autenticar contra la API principal
        try:
            response = requests.post(
                f"{Config.API_BASE_URL}/api/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    return BackofficeUser(
                        id=data['user']['id'],
                        username=data['user']['username'],
                        role=data['user']['role']
                    )
        except requests.RequestException:
            pass
        
        # Fallback to local admin (solo para desarrollo)
        if (username == Config.ADMIN_USERNAME and 
            password == Config.ADMIN_PASSWORD):
            return BackofficeUser(
                id="admin-local",
                username=Config.ADMIN_USERNAME,
                role="admin"
            )
        
        return None
    
    @staticmethod
    def get(user_id):
        # Obtener usuario de la API
        try:
            response = requests.get(
                f"{Config.API_BASE_URL}/api/users/{user_id}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return BackofficeUser(
                    id=data['id'],
                    username=data['username'],
                    role=data['role']
                )
        except requests.RequestException:
            pass
        
        return None