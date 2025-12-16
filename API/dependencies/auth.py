"""
Auth Dependencies - FastAPI dependencies for authentication
==========================================================
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from utils.jwt import decode_jwt
from database import Database


security = HTTPBearer()
db = Database()


async def require_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependencia para requerir usuario autenticado
    
    Args:
        credentials: Credenciales del header Authorization
        
    Returns:
        Dict con datos del usuario
        
    Raises:
        HTTPException: Si el token no es válido
    """
    token = credentials.credentials
    
    # Decodificar token
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )
    
    username = payload.get("username")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin información de usuario"
        )
    
    # Verificar que el usuario existe
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    # Retornar datos del usuario
    return {
        "username": username,
        "role": user.get("role", "user"),
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name")
    }


async def require_admin(
    user_data: Dict[str, Any] = Depends(require_user)
) -> Dict[str, Any]:
    """
    Dependencia para requerir usuario admin
    
    Args:
        user_data: Datos del usuario autenticado
        
    Returns:
        Dict con datos del usuario admin
        
    Raises:
        HTTPException: Si el usuario no es admin
    """
    if user_data.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requiere permisos de administrador"
        )
    
    return user_data


async def optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> Dict[str, Any]:
    """
    Dependencia para usuario opcional (no requiere autenticación)
    
    Args:
        credentials: Credenciales opcionales del header Authorization
        
    Returns:
        Dict con datos del usuario si está autenticado, dict vacío si no
    """
    if not credentials:
        return {}
    
    token = credentials.credentials
    payload = decode_jwt(token)
    
    if not payload:
        return {}
    
    username = payload.get("username")
    if not username:
        return {}
    
    # Verificar que el usuario existe
    user = await db.users.find_one({"username": username})
    if not user:
        return {}
    
    return {
        "username": username,
        "role": user.get("role", "user"),
        "user_id": str(user["_id"]),
        "email": user.get("email"),
        "name": user.get("name")
    }