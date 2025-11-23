from flask_login import UserMixin
import requests
import jwt
from config import Config

class BackofficeUser(UserMixin):
    def __init__(self, id, username, email, role, mfa_enabled=False, mfa_secret="", token=""):
        # 🔥 VALIDACIÓN: No permitir IDs ficticios
        if not id or id in ['None', 'admin-fallback', 'admin-local']:
            raise ValueError(f"ID de usuario inválido: {id}")
            
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
                    access_token = data['access_token']
                    
                    print(f"✅ Login exitoso para {username}: {user_data['username']}")
                    
                    # 🔥 CORRECCIÓN CRÍTICA: Extraer user_id REAL del JWT
                    try:
                        decoded_token = jwt.decode(access_token, options={"verify_signature": False})
                        real_user_id = decoded_token.get('user_id')
                        print(f"🎯 User ID real extraído del JWT: {real_user_id}")
                        
                        # 🔥 VALIDAR que el ID es real
                        if not real_user_id or real_user_id in ['None', 'admin-fallback', 'admin-local']:
                            print(f"❌ ID inválido del JWT: {real_user_id}")
                            return None
                            
                    except Exception as e:
                        print(f"⚠️ No se pudo decodificar JWT: {e}")
                        return None
                    
                    # 🔥 USAR SOLO EL ID REAL - NUNCA FALLBACKS
                    return BackofficeUser(
                        id=real_user_id,  # ← SOLO ID REAL
                        username=user_data['username'],
                        email=user_data['email'],
                        role=user_data['role'],
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=access_token
                    )
                    
        except requests.RequestException as e:
            print(f"❌ Error de conexión: {e}")
        except Exception as e:
            print(f"❌ Error inesperado en authenticate: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"❌ Autenticación fallida para {username}")
        return None
    
    @staticmethod
    def get(user_id, token=None):
        """Obtener usuario por ID REAL - SIN FALLBACKS"""
        print(f"🔍 BackofficeUser.get llamado con user_id: '{user_id}'")
        
        # 🔥 VALIDACIÓN: Rechazar IDs ficticios inmediatamente
        if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
            print(f"❌ ID de usuario inválido: {user_id}")
            return None
        
        try:
            if not token:
                print(f"❌ No token provided for user {user_id}")
                return None
            
            headers = {'Authorization': f'Bearer {token}'}
            print(f"🔍 Obteniendo usuario REAL {user_id} desde API")
            
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
                    print(f"✅ Usuario REAL {user_id} obtenido correctamente desde API")
                    
                    # 🔥 USAR SOLO DATOS REALES DE LA API
                    return BackofficeUser(
                        id=user_data.get('id') or user_data.get('_id') or user_id,
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
        except Exception as e:
            print(f"❌ Error inesperado obteniendo usuario {user_id}: {e}")
        
        print(f"❌ No se pudo obtener usuario REAL {user_id} desde API")
        return None

    @staticmethod
    def get_user_progress(user_id, token):
        """Obtener progreso detallado de un usuario REAL"""
        # 🔥 VALIDAR ID primero
        if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
            print(f"❌ ID inválido para progreso: {user_id}")
            return None
            
        try:
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            print(f"📊 Obteniendo progreso para usuario REAL {user_id}")
            
            response = requests.get(
                f"{Config.API_BASE_URL}/api/users/{user_id}/progress",
                headers=headers,
                timeout=10
            )
            
            print(f"📡 GET /api/users/{user_id}/progress Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    progress_data = data.get('progress', {})
                    print(f"✅ Progreso obtenido para {user_id}")
                    return progress_data
                else:
                    print(f"❌ Error API: {data.get('detail')}")
            else:
                print(f"❌ Error HTTP {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo progreso: {e}")
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
        """Crear usuario desde diccionario de sesión"""
        if not data or not data.get('id'):
            return None
            
        # 🔥 VALIDAR que el ID no sea ficticio
        user_id = data.get('id')
        if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
            print(f"❌ ID ficticio en sesión: {user_id}")
            return None
            
        return cls(
            id=user_id,
            username=data.get('username'),
            email=data.get('email'),
            role=data.get('role'),
            mfa_enabled=data.get('mfa_enabled', False),
            mfa_secret=data.get('mfa_secret', ''),
            token=data.get('token', '')
        )

    def __repr__(self):
        return f"<BackofficeUser {self.username} (ID: {self.id})>"