from flask_login import UserMixin
from config import Config
import requests
import jwt
from datetime import datetime

class BackofficeUser(UserMixin):
    def __init__(self, id, username, email, role, mfa_enabled=False, token=None):
        self.id = id
        self.username = username
        self.email = email
        self.role = role
        self.mfa_enabled = mfa_enabled
        self.token = token

    def get_id(self):
        return self.id

    @staticmethod
    def authenticate(username, password, mfa_code=None):
        """Autenticar usuario, con MFA opcional para casos especiales"""
        try:
            print(f"🔐 Intentando login en: {Config.API_BASE_URL}/api/login")
            print(f"🔍 MFA code proporcionado: {'Sí' if mfa_code else 'No'}")
            
            # Construir payload base
            payload = {"username": username, "password": password}
            
            # Solo incluir MFA si se proporciona
            if mfa_code:
                payload["mfa_token"] = mfa_code
                print(f"🔐 Enviando código MFA con login")
            else:
                print(f"🔓 Login solo con usuario/contraseña (sin MFA)")
            
            response = requests.post(
                f"{Config.API_BASE_URL}/api/login",
                json=payload,
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
                        token=access_token
                    )
                else:
                    print(f"❌ Login rechazado: {data.get('detail', 'Sin detalle')}")
                    return None
            elif response.status_code == 401:
                print("❌ Credenciales inválidas")
                return None
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Detalle: {error_data}")
                except:
                    print(f"   Respuesta: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Error en authenticate: {e}")
            return None

    @staticmethod
    def get(user_id, token=None):
        """Obtener datos del usuario desde la API usando ID"""
        try:
            # 🔥 VALIDAR ID primero
            if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
                print(f"❌ ID inválido para get: {user_id}")
                return None
                
            headers = {}
            if token:
                headers['Authorization'] = f'Bearer {token}'
                
            print(f"🔍 Obteniendo datos para usuario ID: {user_id}")
            
            response = requests.get(
                f"{Config.API_BASE_URL}/api/users/{user_id}",
                headers=headers,
                timeout=5
            )
            
            print(f"📡 Get user response: {response.status_code}")
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Datos de usuario obtenidos para ID: {user_id}")
                
                return BackofficeUser(
                    id=user_id,  # ← USAR EL ID PASADO (debe ser real)
                    username=user_data['username'],
                    email=user_data['email'],
                    role=user_data['role'],
                    mfa_enabled=user_data.get('mfa_enabled', False),
                    token=token
                )
            else:
                print(f"❌ Error obteniendo usuario {user_id}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error en get user: {e}")
            return None

    def to_dict(self):
        """Convertir a diccionario para sesión"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'mfa_enabled': self.mfa_enabled,
            'token': self.token
        }

    @staticmethod
    def from_dict(data):
        """Crear instancia desde diccionario de sesión"""
        if not data:
            return None
            
        # 🔥 VALIDAR ID antes de crear usuario
        user_id = data.get('id')
        if not user_id or user_id in ['None', 'admin-fallback', 'admin-local']:
            print(f"❌ ID inválido en from_dict: {user_id}")
            return None
            
        return BackofficeUser(
            id=user_id,
            username=data.get('username'),
            email=data.get('email'),
            role=data.get('role'),
            mfa_enabled=data.get('mfa_enabled', False),
            token=data.get('token')
        )

    def __repr__(self):
        return f'<BackofficeUser {self.username}>'