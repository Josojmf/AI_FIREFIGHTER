"""
Auth Dependencies - Reusable authentication dependencies
=====================================================
CORREGIDO: Sin importación circular
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

# Importar Database directamente
from database import Database

load_dotenv()

# Configuración JWT
JWT_SECRET = os.getenv("JWT_SECRET", "firefighter-super-secret-jwt-key-2024")

# Security scheme
security = HTTPBearer()

# Crear instancia local de Database
db = Database()

# ============================================================================
# JWT UTILS LOCALES
# ============================================================================

def decode_jwt(token: str) -> dict:
    """Decodificar token JWT"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

# ============================================================================
# DEPENDENCIES
# ============================================================================

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Requerir usuario autenticado"""
    token = credentials.credentials
    payload = decode_jwt(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    username = payload.get("username")
    user_id = payload.get("user_id")
    
    if not username:
        raise HTTPException(status_code=401, detail="Token incompleto")
    
    # Verificar que el usuario existe en la base de datos
    try:
        user = await db.users.find_one({"username": username})
        if not user:
            user = await db.admin_users.find_one({"username": username})
        
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        # Verificar que el usuario está activo
        if user.get("status") != "active":
            raise HTTPException(status_code=401, detail="Cuenta desactivada")
        
        return {
            "username": username,
            "role": user.get("role", "user"),
            "user_id": user_id or str(user["_id"])
        }
    
    except Exception as e:
        print(f"❌ Error verificando usuario: {e}")
        raise HTTPException(status_code=401, detail="Error de autenticación")

async def require_admin(user_data: Dict = Depends(require_user)) -> Dict:
    """Requerir usuario administrador"""
    if user_data.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Requiere permisos de administrador"
        )
    return user_data

async def optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Usuario opcional - No lanza error si no hay token"""
    try:
        return await require_user(credentials)
    except HTTPException:
        return None