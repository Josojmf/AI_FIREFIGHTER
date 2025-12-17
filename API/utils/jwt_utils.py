"""
JWT Utilities - Funciones unificadas para manejo de tokens JWT
==============================================================
Combinación de jwt.py y jwt_utils.py originales
"""

import os
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configuración
JWT_SECRET = os.getenv("SECRET_KEY", "firefighter-secret-key-2024")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))
JWT_ALGORITHM = "HS256"


def make_jwt(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT a partir de un payload.
    
    Args:
        payload: Datos a incluir en el token
        expires_delta: Delta de tiempo para expiración (opcional)
        
    Returns:
        str: Token JWT firmado
    """
    to_encode = payload.copy()
    now = datetime.utcnow()
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=JWT_EXPIRES_HOURS)
    
    to_encode.update({"iat": now, "exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodifica un token JWT.
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Optional[Dict]: Payload decodificado o None si es inválido
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except ExpiredSignatureError:
        print("Token expirado")
        return None
    except InvalidTokenError:
        print("Token inválido")
        return None
    except Exception as e:
        print(f"Error al decodificar token: {e}")
        return None


def verify_jwt(token: str) -> bool:
    """
    Verifica si un token JWT es válido.
    
    Args:
        token: Token JWT a verificar
        
    Returns:
        bool: True si el token es válido, False en caso contrario
    """
    try:
        decode_jwt(token)
        return True
    except Exception:
        return False


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene información del usuario a partir de un token JWT.
    
    Args:
        token: Token JWT
        
    Returns:
        Optional[Dict]: Datos del usuario o None si es inválido
    """
    payload = decode_jwt(token)
    if payload:
        return {
            "username": payload.get("username"),
            "role": payload.get("role", "user"),
            "user_id": payload.get("user_id")
        }
    return None


def create_access_token(username: str, role: str = "user", user_id: Optional[str] = None) -> str:
    """
    Crea un token de acceso para un usuario.
    
    Args:
        username: Nombre de usuario
        role: Rol del usuario (user/admin)
        user_id: ID del usuario en la base de datos
        
    Returns:
        str: Token JWT
    """
    payload = {
        "username": username,
        "role": role,
        "type": "access_token"
    }
    
    if user_id:
        payload["user_id"] = user_id
        
    return make_jwt(payload)


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifica un token de acceso.
    
    Args:
        token: Token JWT
        
    Returns:
        Optional[Dict]: Datos del usuario o None si es inválido
    """
    payload = decode_jwt(token)
    if payload and payload.get("type") == "access_token":
        return payload
    return None