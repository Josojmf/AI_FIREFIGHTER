# app/models/user.py (VERSIÓN COMPLETAMENTE CORREGIDA)
from flask_login import UserMixin
import requests
from config import Config

class BackofficeUser(UserMixin):
    def __init__(self, id, username, email, role, mfa_enabled=False, mfa_secret="", token=""):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.mfa_enabled = mfa_enabled
        self.mfa_secret = mfa_secret
        self.token = token  # ✅ NUEVO: Token JWT para autenticación API
    
    @staticmethod
    def authenticate(username, password):
        try:
            response = requests.post(
                f"{Config.API_BASE_URL}/api/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    user_data = data['user']
                    return BackofficeUser(
                        id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        role=user_data['role'],
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=data['access_token']  # ✅ GUARDAR TOKEN JWT
                    )
        except requests.RequestException as e:
            print(f"Auth error: {e}")
        
        # Fallback to local admin (SOLO PARA DESARROLLO)
        if (username == Config.ADMIN_USERNAME and 
            password == Config.ADMIN_PASSWORD):
            return BackofficeUser(
                id="admin-local",
                username=Config.ADMIN_USERNAME,
                email="admin@local",
                role="admin",
                mfa_enabled=False,
                mfa_secret="",
                token="local-admin-token"  # ✅ TOKEN PARA ADMIN LOCAL
            )
        
        return None
    
    @staticmethod
    def get(user_id, token=None):
        """Obtener usuario por ID con autenticación"""
        try:
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            
            response = requests.get(
                f"{Config.API_BASE_URL}/api/users/{user_id}",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    user_data = data.get('user', {})
                    return BackofficeUser(
                        id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        role=user_data.get('role'),
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=token  # ✅ MANTENER EL TOKEN
                    )
        except requests.RequestException as e:
            print(f"Error getting user {user_id}: {e}")
        
        # Fallback para admin local
        if user_id == "admin-local":
            return BackofficeUser(
                id="admin-local",
                username=Config.ADMIN_USERNAME,
                email="admin@local",
                role="admin",
                mfa_enabled=False,
                mfa_secret="",
                token="local-admin-token"
            )
        
        return None

    def to_dict(self):
        """Convertir usuario a diccionario para sesión"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'mfa_enabled': self.mfa_enabled,
            'mfa_secret': self.mfa_secret,
            'token': self.token
        }

    @classmethod
    def from_dict(cls, data):
        """Crear usuario desde diccionario"""
        return cls(
            id=data.get('id'),
            username=data.get('username'),
            email=data.get('email'),
            role=data.get('role'),
            mfa_enabled=data.get('mfa_enabled', False),
            mfa_secret=data.get('mfa_secret', ''),
            token=data.get('token', '')
        )