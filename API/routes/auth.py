"""
Auth Routes - Authentication endpoints PARA PRODUCCIÓN
=======================================================
Versión compatible con Docker, Swarm y Backoffice
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Optional, Dict, Any
import bcrypt
import os
from utils.jwt_utils import make_jwt, decode_jwt

router = APIRouter()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

JWT_SECRET = os.getenv("SECRET_KEY", "firefighter-secret-key-2024")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# ============================================================================
# PYDANTIC MODELS (importar desde models)
# ============================================================================

from models.auth_models import (
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    ChangePasswordRequest
)

# ============================================================================
# UTILS
# ============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, pwd_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), pwd_hash.encode("utf-8"))
    except:
        return False

def make_jwt(payload: dict) -> str:
    now = datetime.utcnow()
    exp = now + timedelta(hours=JWT_EXPIRES_HOURS)
    to_encode = {**payload, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

def decode_jwt(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except:
        return None

# ============================================================================
# AUTH DEPENDENCY
# ============================================================================

security = HTTPBearer()

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency para requerir usuario autenticado"""
    from api import db
    
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    username = payload.get("username")
    user = await db.users.find_one({"username": username})
    if not user:
        user = await db.admin_users.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return {
        "username": username,
        "role": user.get("role", "user"),
        "user_id": str(user["_id"])
    }

async def require_admin(user_data: dict = Depends(require_user)) -> dict:
    if user_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")
    return user_data

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/login")
async def login(request: LoginRequest):
    """Login endpoint - COMPATIBLE con backoffice y Docker"""
    from api import db
    
    try:
        username = request.username.strip()
        password = request.password

        if not username or not password:
            raise HTTPException(status_code=400, detail="Usuario y contraseña requeridos")

        print(f"🔐 Login intento para: {username}")

        # Buscar usuario en admin_users primero, luego en users
        query = {"$or": [{"username": username.lower()}, {"email": username.lower()}]}
        user_doc = await db.admin_users.find_one(query)
        if not user_doc:
            user_doc = await db.users.find_one(query)

        if not user_doc:
            print(f"❌ Usuario no encontrado: {username}")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Verificar contraseña (soporta ambos formatos)
        password_field = None
        for field in ["password_hash", "password"]:
            if field in user_doc:
                password_field = field
                break
        
        if not password_field or not verify_password(password, user_doc[password_field]):
            print(f"❌ Contraseña incorrecta para: {username}")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        # Verificar estado
        if user_doc.get("status") != "active":
            raise HTTPException(status_code=401, detail="Cuenta desactivada")

        # Verificar MFA si está habilitado
        if user_doc.get("mfa_enabled", False):
            if not request.mfa_token:
                raise HTTPException(status_code=401, detail="Token MFA requerido")
            # Aquí implementar verificación MFA

        # Actualizar último login
        update_op = {"$set": {"last_login": datetime.utcnow()}}
        if "admin_users" in str(db.admin_users) and user_doc.get("_id"):
            await db.admin_users.update_one({"_id": user_doc["_id"]}, update_op)
        else:
            await db.users.update_one({"_id": user_doc["_id"]}, update_op)

        # Crear JWT - VERSIÓN COMPATIBLE
        token_payload = {
            "user_id": str(user_doc["_id"]),
            "username": user_doc["username"],
            "role": user_doc.get("role", "user"),
            "type": "access_token"
        }
        
        token = make_jwt(token_payload)

        print(f"✅ Login exitoso para: {username}")

        # 🔥 RESPUESTA COMPATIBLE con Docker Swarm y Backoffice
        return {
            "ok": True,
            "access_token": token,
            "token": token,  # Alias para compatibilidad
            "user": {
                "id": str(user_doc["_id"]),
                "username": user_doc["username"],
                "email": user_doc.get("email", ""),
                "name": user_doc.get("name", ""),
                "role": user_doc.get("role", "user"),
                "mfa_enabled": user_doc.get("mfa_enabled", False),
                "status": user_doc.get("status", "active")
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en login: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/register")
async def register(request: RegisterRequest):
    """Register endpoint"""
    from api import db
    
    try:
        username = request.username.strip().lower()
        email = request.email.strip().lower()
        
        print(f"📝 Registro intento para: {username} ({email})")
        
        # Verificar duplicados
        existing = await db.users.find_one({
            "$or": [{"username": username}, {"email": email}]
        })
        if existing:
            raise HTTPException(status_code=409, detail="Usuario o email ya existe")
        
        # Crear usuario
        user_doc = {
            "_id": str(uuid4()),
            "username": username,
            "email": email,
            "name": request.name,
            "password_hash": hash_password(request.password),
            "role": "user",
            "status": "active",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "email_verified": False,
            "mfa_enabled": False,
            "metadata": {}
        }
        
        await db.users.insert_one(user_doc)
        
        # Crear token automáticamente
        token_payload = {
            "user_id": user_doc["_id"],
            "username": username,
            "role": "user"
        }
        token = make_jwt(token_payload)
        
        print(f"✅ Usuario registrado: {username}")
        
        return {
            "ok": True,
            "access_token": token,
            "detail": "Cuenta creada exitosamente",
            "user": {
                "id": user_doc["_id"],
                "username": username,
                "email": email,
                "role": "user"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en registro: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.post("/forgot-password")
async def forgot_password(request: PasswordResetRequest):
    """Solicitar reset de contraseña"""
    from api import db
    from secrets import token_urlsafe
    
    try:
        email = request.email.lower().strip()
        
        # Buscar usuario
        user = await db.users.find_one({"email": email})
        if not user:
            # Por seguridad, no revelar si el email existe
            return {
                "ok": True,
                "detail": "Si el email existe, recibirás instrucciones"
            }
        
        # Generar token de reset
        reset_token = token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        reset_doc = {
            "token": reset_token,
            "user_id": user["_id"],
            "email": email,
            "created_at": datetime.utcnow(),
            "expiresAt": expires_at,
            "used": False
        }
        
        await db.resets.insert_one(reset_doc)
        
        # TODO: Enviar email en producción
        if os.getenv("ENVIRONMENT") == "production":
            print(f"📧 Enviando email de reset a: {email}")
        else:
            print(f"🔑 Token de reset (DEV): {reset_token}")
        
        return {
            "ok": True,
            "detail": "Si el email existe, recibirás instrucciones"
        }
        
    except Exception as e:
        print(f"❌ Error en forgot-password: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.post("/reset-password")
async def reset_password(request: PasswordResetConfirm):
    """Resetear contraseña con token"""
    from api import db
    
    try:
        # Buscar token
        reset = await db.resets.find_one({"token": request.token, "used": False})
        
        if not reset:
            raise HTTPException(status_code=400, detail="Token inválido o ya usado")
        
        if datetime.utcnow() > reset["expiresAt"]:
            raise HTTPException(status_code=400, detail="Token expirado")
        
        # Actualizar contraseña
        new_hash = hash_password(request.new_password)
        
        await db.users.update_one(
            {"_id": reset["user_id"]},
            {"$set": {"password_hash": new_hash}}
        )
        
        # Marcar token como usado
        await db.resets.update_one(
            {"token": request.token},
            {"$set": {"used": True}}
        )
        
        return {
            "ok": True,
            "detail": "Contraseña actualizada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en reset-password: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user_data: Dict[str, Any] = Depends(require_user)
):
    """Cambiar contraseña (requiere autenticación)"""
    from api import db
    
    try:
        username = user_data["username"]
        user_id = user_data["user_id"]
        
        print(f"🔐 Cambio de contraseña para: {username}")
        
        # Buscar usuario
        user = await db.users.find_one({"username": username})
        if not user:
            user = await db.admin_users.find_one({"username": username})
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar contraseña actual
        password_field = "password_hash" if "password_hash" in user else "password"
        if not verify_password(request.old_password, user[password_field]):
            raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
        
        # Actualizar contraseña
        new_hash = hash_password(request.new_password)
        
        if "admin_users" in str(db.admin_users) and user.get("role") == "admin":
            await db.admin_users.update_one(
                {"username": username},
                {"$set": {password_field: new_hash}}
            )
        else:
            await db.users.update_one(
                {"username": username},
                {"$set": {password_field: new_hash}}
            )
        
        return {
            "ok": True,
            "detail": "Contraseña actualizada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en change-password: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.get("/me")
async def get_current_user(user_data: Dict[str, Any] = Depends(require_user)):
    """Obtener información del usuario actual"""
    from api import db
    
    try:
        username = user_data["username"]
        
        user = await db.users.find_one({"username": username})
        if not user:
            user = await db.admin_users.find_one({"username": username})
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {
            "ok": True,
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user.get("email", ""),
                "role": user.get("role", "user"),
                "mfa_enabled": user.get("mfa_enabled", False),
                "status": user.get("status", "active"),
                "created_at": user.get("created_at"),
                "last_login": user.get("last_login")
            }
        }
        
    except Exception as e:
        print(f"❌ Error en /me: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.get("/health")
async def auth_health():
    """Health check para el router de auth"""
    return {
        "ok": True,
        "service": "auth",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }