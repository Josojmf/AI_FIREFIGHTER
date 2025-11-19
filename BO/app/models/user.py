# app/models/user.py - Modelo de usuario completamente corregido
from flask_login import UserMixin
import requests
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class BackofficeUser(UserMixin):
    def __init__(self, id, username, email, role, mfa_enabled=False, mfa_secret="", token="", **kwargs):
        self.id = str(id)  # Asegurar que el ID sea string
        self.username = username
        self.email = email
        self.role = role
        self.mfa_enabled = mfa_enabled
        self.mfa_secret = mfa_secret
        self.token = token
        
        # Campos adicionales
        self.status = kwargs.get('status', 'active')
        self.created_at = kwargs.get('created_at')
        self.last_login = kwargs.get('last_login')
    
    def get_id(self):
        """Método requerido por Flask-Login"""
        return self.id
    
    @staticmethod
    def authenticate(username, password):
        """Autenticar usuario contra la API principal"""
        try:
            api_url = current_app.config['API_BASE_URL']
            logger.info(f"🔐 Intentando login en: {api_url}/api/login")
            
            # Hacer request a la API
            response = requests.post(
                f"{api_url}/api/login",
                json={
                    "username": username.strip(),
                    "password": password
                },
                timeout=15,
                headers={'Content-Type': 'application/json'}
            )
            
            logger.info(f"📡 Respuesta API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"📋 Datos recibidos: {data.keys() if isinstance(data, dict) else type(data)}")
                
                if data.get('ok') and data.get('user'):
                    user_data = data['user']
                    access_token = data.get('access_token', '')
                    
                    # Verificar que el usuario tenga rol admin
                    user_role = user_data.get('role', 'user')
                    if user_role != 'admin':
                        logger.warning(f"❌ Usuario {username} no tiene rol admin (rol: {user_role})")
                        return None
                    
                    logger.info(f"✅ Login exitoso para admin: {username}")
                    return BackofficeUser(
                        id=user_data.get('_id', user_data.get('id')),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        role=user_role,
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=access_token,
                        status=user_data.get('status', 'active'),
                        created_at=user_data.get('created_at'),
                        last_login=user_data.get('last_login')
                    )
                else:
                    logger.warning(f"❌ Respuesta API inválida: {data}")
            
            elif response.status_code == 401:
                logger.warning(f"❌ Credenciales incorrectas para: {username}")
            else:
                logger.error(f"❌ Error API {response.status_code}: {response.text}")
                
        except requests.RequestException as e:
            logger.error(f"❌ Error de conexión API: {e}")
        except Exception as e:
            logger.error(f"❌ Error inesperado en autenticación: {e}")
        
        # Fallback a admin local (solo para desarrollo)
        return BackofficeUser._try_local_admin(username, password)
    
    @staticmethod
    def _try_local_admin(username, password):
        """Fallback a admin local para desarrollo"""
        config_username = current_app.config.get('ADMIN_USERNAME', 'admin')
        config_password = current_app.config.get('ADMIN_PASSWORD', 'admin123')
        
        if username == config_username and password == config_password:
            logger.info(f"🔧 Login local exitoso para: {username}")
            return BackofficeUser(
                id="admin-local",
                username=config_username,
                email="admin@local.dev",
                role="admin",
                mfa_enabled=False,
                mfa_secret="",
                token="local-admin-token",
                status="active"
            )
        
        logger.warning(f"❌ Todas las formas de autenticación fallaron para: {username}")
        return None
    
    @staticmethod
    def get(user_id, token=None):
        """Obtener usuario por ID"""
        try:
            # Verificar si es admin local
            if user_id == "admin-local":
                config_username = current_app.config.get('ADMIN_USERNAME', 'admin')
                return BackofficeUser(
                    id="admin-local",
                    username=config_username,
                    email="admin@local.dev",
                    role="admin",
                    mfa_enabled=False,
                    mfa_secret="",
                    token="local-admin-token",
                    status="active"
                )
            
            # Intentar obtener desde API
            api_url = current_app.config['API_BASE_URL']
            headers = {}
            
            if token and token != "local-admin-token":
                headers['Authorization'] = f'Bearer {token}'
            
            response = requests.get(
                f"{api_url}/api/users/{user_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('user'):
                    user_data = data['user']
                    return BackofficeUser(
                        id=user_data.get('_id', user_data.get('id')),
                        username=user_data.get('username'),
                        email=user_data.get('email'),
                        role=user_data.get('role', 'user'),
                        mfa_enabled=user_data.get('mfa_enabled', False),
                        mfa_secret=user_data.get('mfa_secret', ''),
                        token=token,
                        status=user_data.get('status', 'active'),
                        created_at=user_data.get('created_at'),
                        last_login=user_data.get('last_login')
                    )
            
            logger.warning(f"❌ No se pudo obtener usuario {user_id} desde API")
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo usuario {user_id}: {e}")
        
        return None

    def to_dict(self):
        """Convertir usuario a diccionario para serialización"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'mfa_enabled': self.mfa_enabled,
            'status': self.status,
            'token': self.token
        }

    def __repr__(self):
        return f"<BackofficeUser {self.username} ({self.role})>"