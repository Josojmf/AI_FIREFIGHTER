"""
Auth Routes - Authentication endpoints (STANDALONE)
===================================================
No requiere carpetas models/, utils/, dependencies/ externas
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import bcrypt
import jwt
import os

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

JWT_SECRET = os.getenv("SECRET_KEY", "firefighter-secret-key-2024")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_token: Optional[str] = None

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: EmailStr
    name: str
    access_token: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

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
    from api import db  # Import local para evitar circular
    
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    username = payload.get("username")
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return {
        "username": username,
        "role": user.get("role", "user"),
        "user_id": str(user["_id"])
    }

# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter()

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/login")
async def login(request: LoginRequest):
    """Login endpoint"""
    from api import db  # Import local
    
    try:
        username = request.username.strip()
        password = request.password

        if not username or not password:
            raise HTTPException(status_code=400, detail="Usuario y contraseña requeridos")

        # Buscar usuario
        query = {"$or": [{"username": username.lower()}, {"email": username.lower()}]}
        user_doc = await db.admin_users.find_one(query)
        if not user_doc:
            user_doc = await db.users.find_one(query)

        if not user_doc or not verify_password(password, user_doc["password_hash"]):
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if user_doc.get("status") != "active":
            raise HTTPException(status_code=401, detail="Cuenta desactivada")

        # Actualizar último login
        await db.users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )

        # Crear JWT
        token_payload = {
            "user_id": str(user_doc["_id"]),
            "username": user_doc["username"],
            "role": user_doc.get("role", "user")
        }
        
        token = make_jwt(token_payload)

        return {
            "ok": True,
            "access_token": token,
            "user": {
                "id": str(user_doc["_id"]),
                "username": user_doc["username"],
                "email": user_doc["email"],
                "role": user_doc.get("role", "user"),
                "mfa_enabled": user_doc.get("mfa_enabled", False)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en login: {e}")
        raise HTTPException(status_code=500, detail="Error interno")


@router.post("/register")
async def register(request: RegisterRequest):
    """Register endpoint"""
    from api import db  # Import local
    
    try:
        username = request.username.strip().lower()
        email = request.email.strip().lower()
        
        # Verificar duplicados
        existing = await db.users.find_one({
            "$or": [{"username": username}, {"email": email}]
        })
        if existing:
            raise HTTPException(status_code=409, detail="Usuario o email ya existe")
        
        # Crear usuario con sistema Leitner embebido
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
            "leitner_system": {
                "boxes": {"1": [], "2": [], "3": [], "4": [], "5": [], "6": []},
                "created_at": datetime.utcnow(),
                "last_study": None,
                "total_cards": 0
            }
        }
        
        await db.users.insert_one(user_doc)
        
        return {
            "ok": True,
            "detail": "Cuenta creada exitosamente",
            "username": username,
            "email": email,
            "embedded_structure": True
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
        
        # TODO: Enviar email
        print(f"🔑 Reset token: {reset_token}")
        
        return {
            "ok": True,
            "detail": "Si el email existe, recibirás instrucciones"
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
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
        print(f"❌ Error: {e}")
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
        
        # Buscar usuario
        user = await db.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Verificar contraseña actual
        if not verify_password(request.old_password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Contraseña actual incorrecta")
        
        # Actualizar contraseña
        new_hash = hash_password(request.new_password)
        
        await db.users.update_one(
            {"username": username},
            {"$set": {"password_hash": new_hash}}
        )
        
        return {
            "ok": True,
            "detail": "Contraseña actualizada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail="Error interno")