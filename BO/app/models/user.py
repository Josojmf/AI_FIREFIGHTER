# app/models/user.py (VERSIÓN FINAL CORREGIDA)
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
        self.token = token
    
    @staticmethod
    def authenticate(username, password):
        try:
            print(f"🔐 Intentando login en: {Config.API_BASE_URL}/api/login")
            response = requests.post(
                f"{Config.API_BASE_URL}/api/login",
                json={"username": username, "password": password},
                timeout=10
            )
            
            print(f"📡 Respuesta API: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"📋 Datos recibidos: {list(data.keys())}")
                if data['ok']:
                    user_data = data['user']
                    print(f"✅ Login exitoso para {username}: {user_data['username']}")
                    return BackofficeUser(
                        id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        role=user_data['role'],
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=data['access_token']
                    )
        except requests.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        
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
                token="local-admin-token"
            )
        
        return None
    
    @staticmethod
    def get(user_id, token=None):
        """Obtener usuario por ID con autenticación"""
        try:
            if not token:
                print(f"⚠️ No token provided for user {user_id}")
                # Si no hay token, intentamos con el admin local
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
            
            headers = {'Authorization': f'Bearer {token}'}
            print(f"🔍 Obteniendo usuario {user_id} con token: {token[:10]}...")
            
            response = requests.get(
                f"{Config.API_BASE_URL}/api/users/{user_id}",
                headers=headers,
                timeout=5
            )
            
            print(f"📡 GET /api/users/{user_id} Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    user_data = data.get('user', {})
                    print(f"✅ Usuario {user_id} obtenido correctamente")
                    return BackofficeUser(
                        id=user_data.get('id'),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        role=user_data.get('role'),
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=token
                    )
            else:
                print(f"❌ Error API {response.status_code}: {response.text}")
                
        except requests.RequestException as e:
            print(f"❌ Error de conexión obteniendo usuario {user_id}: {e}")
        
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
        
        print(f"❌ No se pudo obtener usuario {user_id} desde API")
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