"""
User Routes - User management endpoints
=======================================
CORREGIDO: Sin importación circular + Endpoints MFA
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId
import pyotp
import base64
import qrcode
import io

# IMPORTAR Database directamente (no desde api.py)
from database import Database

router = APIRouter()

# ============================================================================
# UTILS LOCALES - EVITAR IMPORTACIÓN CIRCULAR
# ============================================================================

def serialize_doc(doc):
    """Serializar documento MongoDB - función local"""
    if not doc:
        return None
    if "_id" in doc:
        if isinstance(doc["_id"], ObjectId):
            doc["id"] = str(doc["_id"])
        else:
            doc["id"] = doc["_id"]
        del doc["_id"]
    return doc

# ============================================================================
# AUTH DEPENDENCIES LOCALES - SIN IMPORTACIÓN CIRCULAR
# ============================================================================

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "firefighter-super-secret-jwt-key-2024")
security = HTTPBearer()

def decode_jwt_local(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None

async def require_user_local(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    token = credentials.credentials
    payload = decode_jwt_local(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    username = payload.get("username")

    # Buscar usuario usando Database (colecciones ya inicializadas en connect_db)
    user = await Database.users.find_one({"username": username})
    if not user:
        user = await Database.admin_users.find_one({"username": username})

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return {
        "username": username,
        "role": user.get("role", "user"),
        "user_id": str(user["_id"]) if "_id" in user else user.get("id", ""),
    }

async def require_admin_local(user_data: dict = Depends(require_user_local)) -> dict:
    if user_data.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Requiere permisos de administrador")
    return user_data

# ============================================================================
# HELPERS MFA
# ============================================================================

def build_otpauth_uri(secret: str, username: str, issuer: str = "FirefighterAI") -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)

def make_qr_base64(otpauth_uri: str) -> str:
    img = qrcode.make(otpauth_uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

async def _find_user_by_id_any_collection(user_id: str):
    """Buscar usuario por _id en users o admin_users."""
    user = None
    try:
        oid = ObjectId(user_id)
        user = await Database.users.find_one({"_id": oid})
        if not user:
            user = await Database.admin_users.find_one({"_id": oid})
    except InvalidId:
        # Intento directo por string
        user = await Database.users.find_one({"_id": user_id})
        if not user:
            user = await Database.admin_users.find_one({"_id": user_id})
    return user

async def _update_user_any_collection(user, update: Dict[str, Any]):
    """Actualizar usuario en la colección correcta según exista en users o admin_users."""
    _id = user["_id"]
    # Intentar en users
    result = await Database.users.update_one({"_id": _id}, {"$set": update})
    if result.matched_count == 0:
        # Intentar en admin_users
        result = await Database.admin_users.update_one({"_id": _id}, {"$set": update})
    return result

# ============================================================================
# ENDPOINTS MFA
# ============================================================================

@router.post("/users/{user_id}/mfa/generate", response_model=Dict[str, Any])
async def generate_mfa_secret(user_id: str, user_data: Dict = Depends(require_user_local)):
    """
    Generar secreto MFA + QR + clave manual.
    Endpoint esperado por el backoffice: POST /api/users/{user_id}/mfa/generate
    """
    print(f"🔍 DEBUG Generate MFA para user_id={user_id}")
    
    # Solo el propio usuario o admin
    if user_data.get("role") != "admin" and user_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    user = await _find_user_by_id_any_collection(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Generar secreto TOTP
    secret = pyotp.random_base32()
    print(f"🔍 Secreto generado: {secret}")
    
    username_label = user.get("email") or user.get("username", "usuario")
    otpauth_uri = build_otpauth_uri(secret, username_label)
    qrcode_b64 = make_qr_base64(otpauth_uri)

    # Guardar secreto en BD
    update_result = await _update_user_any_collection(user, {
        "mfa_secret": secret,
        "mfa_enabled": False,
        "mfa_created_at": datetime.utcnow(),
    })
    
    print(f"🔍 Secreto guardado en BD: modificados={update_result.modified_count}")

    return {
        "ok": True,
        "secret": secret,
        "qrcode": qrcode_b64,    
        "manual_entry_key": secret
    }

@router.post("/users/{user_id}/mfa/verify-setup", response_model=Dict[str, Any])
async def verify_mfa_setup(user_id: str, body: Dict[str, Any], user_data: Dict = Depends(require_user_local)):
    """
    Verificar código MFA durante el setup.
    Endpoint esperado: POST /api/users/{user_id}/mfa/verify-setup
    """
    code = str(body.get("code", "")).strip()
    print(f"🔍 DEBUG MFA Verify Setup para user_id={user_id}")
    print(f"🔍 Código recibido: {code}")
    
    if not (code.isdigit() and len(code) == 6):
        print(f"❌ Código inválido: {code}")
        raise HTTPException(status_code=400, detail="Código MFA inválido")

    # Solo el propio usuario o admin
    if user_data.get("role") != "admin" and user_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    user = await _find_user_by_id_any_collection(user_id)
    print(f"🔍 Usuario encontrado: {user is not None}")
    
    if not user:
        print(f"❌ Usuario no encontrado: {user_id}")
        return {"ok": False, "detail": "Usuario no encontrado"}
    
    if "mfa_secret" not in user:
        print(f"❌ No hay secreto MFA para usuario: {user_id}")
        print(f"🔍 Campos del usuario: {list(user.keys())}")
        return {"ok": False, "detail": "MFA no inicializado"}

    # Debug: Mostrar el secreto (en logs solo, no en producción real)
    print(f"🔍 Secreto MFA presente: {'SÍ' if user.get('mfa_secret') else 'NO'}")
    print(f"🔍 Tiempo actual UTC: {datetime.utcnow().isoformat()}")
    
    totp = pyotp.TOTP(user["mfa_secret"])
    
    # Verificar con margen de tiempo más amplio
    is_valid = totp.verify(code, valid_window=2)  # ±2 intervalos (60 segundos)
    
    print(f"🔍 Verificación TOTP: código={code}, válido={is_valid}")
    
    if not is_valid:
        # Generar código actual para comparar
        current_code = totp.now()
        print(f"🔍 Código actual esperado: {current_code}")
        print(f"🔍 Diferencia: {abs(int(code) - int(current_code)) if current_code.isdigit() else 'N/A'}")
        return {"ok": False, "detail": "Código MFA incorrecto"}

    # Marcar MFA como habilitado
    result = await _update_user_any_collection(user, {
        "mfa_enabled": True,
        "mfa_verified_at": datetime.utcnow(),
    })
    
    print(f"🔍 MFA habilitado: modificados={result.modified_count}")
    
    return {"ok": True, "detail": "MFA configurado exitosamente"}

@router.post("/users/{user_id}/mfa/verify", response_model=Dict[str, Any])
async def verify_mfa(user_id: str, body: Dict[str, Any]):
    """
    Verificar código MFA normal (login).
    Endpoint esperado: POST /api/users/{user_id}/mfa/verify
    """
    code = str(body.get("code", "")).strip()
    if not (code.isdigit() and len(code) == 6):
        raise HTTPException(status_code=400, detail="Código MFA inválido")

    user = await _find_user_by_id_any_collection(user_id)
    if not user or not user.get("mfa_enabled") or "mfa_secret" not in user:
        return {"ok": False}

    totp = pyotp.TOTP(user["mfa_secret"])
    return {"ok": bool(totp.verify(code))}

@router.post("/users/{user_id}/mfa/enable", response_model=Dict[str, Any])
async def enable_mfa(user_id: str, user_data: Dict = Depends(require_user_local)):
    """
    Marcar MFA como habilitado (usado por backoffice para asegurar estado).
    Endpoint esperado: POST /api/users/{user_id}/mfa/enable
    """
    if user_data.get("role") != "admin" and user_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    user = await _find_user_by_id_any_collection(user_id)
    if not user or "mfa_secret" not in user:
        raise HTTPException(status_code=400, detail="MFA no inicializado")

    await _update_user_any_collection(user, {
        "mfa_enabled": True,
        "mfa_verified_at": datetime.utcnow(),
    })

    return {"ok": True}

@router.post("/users/{user_id}/mfa/disable", response_model=Dict[str, Any])
async def disable_mfa(user_id: str, user_data: Dict = Depends(require_user_local)):
    """
    Deshabilitar MFA para el usuario.
    Endpoint esperado: POST /api/users/{user_id}/mfa/disable
    """
    if user_data.get("role") != "admin" and user_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    user = await _find_user_by_id_any_collection(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    await _update_user_any_collection(user, {
        "mfa_enabled": False,
        # Opcional: borrar secreto si quieres forzar nuevo setup
        # "mfa_secret": None,
    })

    return {"ok": True}

# ============================================================================
# ENDPOINTS USUARIOS
# ============================================================================

@router.get("/users", response_model=Dict[str, Any])
async def list_users(user_data: Dict = Depends(require_user_local)):
    """Listar todos los usuarios (cualquier usuario autenticado)"""
    try:
        print(f"🔍 GET /api/users - User: {user_data['username']}")
        cursor = Database.users.find(
            {},
            {
                "password": 0,
                "password_hash": 0,
                "mfa_secret": 0,
            },
        )
        users_list = await cursor.to_list(length=1000)

        processed_users = []
        for user in users_list:
            user_data_item = serialize_doc(user)
            user_data_item.setdefault("email_verified", False)
            user_data_item.setdefault("mfa_enabled", False)
            user_data_item.setdefault("has_leitner_progress", False)
            user_data_item.setdefault("has_backoffice_cards", False)
            user_data_item.setdefault("metadata", {})
            user_data_item.setdefault("status", "active")
            user_data_item.setdefault("role", "user")

            for date_field in ["created_at", "last_login"]:
                if (
                    date_field in user_data_item
                    and isinstance(user_data_item[date_field], datetime)
                ):
                    user_data_item[date_field] = user_data_item[date_field].isoformat()

            processed_users.append(user_data_item)

        return {"ok": True, "users": processed_users}
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/users/{userid}", response_model=Dict[str, Any])
async def get_user_by_any(userid: str, userdata: Dict = Depends(require_user_local)):
    """Obtener un usuario por id/username (cualquier usuario autenticado)"""
    try:
        user = None

        # 1) Si es ObjectId válido
        try:
            oid = ObjectId(userid)
            user = await Database.users.find_one({"_id": oid})
        except InvalidId:
            user = None

        # 2) Buscar por _id string
        if not user:
            user = await Database.users.find_one({"_id": userid})

        # 3) Extra: compatibilidad por username
        if not user:
            user = await Database.users.find_one({"username": userid})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        result_user_data = serialize_doc(user)
        result_user_data.setdefault("email_verified", False)
        result_user_data.setdefault("mfa_enabled", False)
        result_user_data.setdefault("has_leitner_progress", False)
        result_user_data.setdefault("has_backoffice_cards", False)
        result_user_data.setdefault("metadata", {})

        return {"ok": True, "user": result_user_data}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/users/me", response_model=Dict[str, Any])
async def get_current_user(user_data: Dict = Depends(require_user_local)):
    """Obtener información del usuario actual"""
    try:
        user_id = user_data.get("user_id")
        try:
            oid = ObjectId(user_id)
            user = await Database.users.find_one({"_id": oid})
        except InvalidId:
            user = await Database.users.find_one({"username": user_data["username"]})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        result_user_data = serialize_doc(user)
        result_user_data.setdefault("email_verified", False)
        result_user_data.setdefault("mfa_enabled", False)
        result_user_data.setdefault("has_leitner_progress", False)
        result_user_data.setdefault("has_backoffice_cards", False)
        result_user_data.setdefault("metadata", {})

        return {"ok": True, "user": result_user_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.patch("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    updates: Dict[str, Any],
    user_data: Dict = Depends(require_user_local),
):
    """Actualizar usuario (propio o admin)"""
    try:
        if user_data.get("role") != "admin" and user_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

        allowed_fields = ["email", "name", "status", "mfa_enabled"]
        if user_data.get("role") == "admin":
            allowed_fields.append("role")

        update_dict = {}
        for field in allowed_fields:
            if field in updates and updates[field] is not None:
                update_dict[field] = updates[field]

        if not update_dict:
            return {"ok": True, "message": "No hay cambios"}

        update_dict["updated_at"] = datetime.utcnow()

        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")

        result = await Database.users.update_one(
            {"_id": oid},
            {"$set": update_dict},
        )

        if result.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Usuario no encontrado o sin cambios"
            )

        return {"ok": True, "message": "Usuario actualizado"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(user_id: str, admin_data: Dict = Depends(require_admin_local)):
    """Eliminar usuario (solo admin)"""
    try:
        if admin_data.get("user_id") == user_id:
            raise HTTPException(
                status_code=400,
                detail="No puedes eliminar tu propia cuenta",
            )

        print(f"🔍 DELETE /api/users/{user_id}")

        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")

        result = await Database.users.update_one(
            {"_id": oid},
            {"$set": {"status": "inactive", "deleted_at": datetime.utcnow()}},
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return {"ok": True, "message": "Usuario desactivado"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando usuario: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/users/{user_id}/progress", response_model=Dict[str, Any])
async def get_user_progress(
    user_id: str, user_data: Dict = Depends(require_user_local)
):
    """Obtener progreso Leitner del usuario (propio o admin)"""
    try:
        if user_data.get("role") != "admin" and user_data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")

        print(f"🔍 GET /api/users/{user_id}/progress")

        try:
            oid = ObjectId(user_id)
            user = await Database.users.find_one({"_id": oid})
        except InvalidId:
            user = await Database.users.find_one({"username": user_id})

        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        leitner = user.get("leitner_system", {})
        boxes = leitner.get("boxes", {})

        progress = {
            "total_cards": sum(len(cards) for cards in boxes.values()),
            "boxes": {str(k): len(v) for k, v in boxes.items()},
            "last_study": leitner.get("last_study"),
            "created_at": leitner.get("created_at"),
            "study_sessions": leitner.get("study_sessions", 0),
            "streak": leitner.get("streak", 0),
            "has_leitner_progress": bool(leitner),
        }

        return {"ok": True, "progress": progress}
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo progreso: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/health/users", response_model=Dict[str, Any])
async def users_health():
    """Health check para router de usuarios"""
    return {
        "ok": True,
        "service": "users",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/debug/mfa/{user_id}")
async def debug_mfa_status(user_id: str):
    """Debug endpoint para verificar estado MFA en todas las colecciones"""
    print(f"🔍 DEBUG MFA STATUS para user_id={user_id}")
    
    from bson import ObjectId
    
    results = {
        "user_id": user_id,
        "found_in": [],
        "details": {}
    }
    
    # Buscar en users
    user_in_users = await Database.users.find_one({"_id": user_id})
    print(f"🔍 En colección 'users': {user_in_users is not None}")
    if user_in_users:
        results["found_in"].append("users")
        results["details"]["users"] = {
            "mfa_enabled": user_in_users.get('mfa_enabled'),
            "has_mfa_secret": 'mfa_secret' in user_in_users,
            "mfa_verified_at": user_in_users.get('mfa_verified_at'),
            "mfa_created_at": user_in_users.get('mfa_created_at')
        }
        print(f"   - mfa_enabled: {user_in_users.get('mfa_enabled')}")
        print(f"   - mfa_secret: {'SÍ' if user_in_users.get('mfa_secret') else 'NO'}")
        print(f"   - mfa_verified_at: {user_in_users.get('mfa_verified_at')}")
        print(f"   - mfa_created_at: {user_in_users.get('mfa_created_at')}")
    
    # Buscar en admin_users
    user_in_admin = await Database.admin_users.find_one({"_id": user_id})
    print(f"🔍 En colección 'admin_users': {user_in_admin is not None}")
    if user_in_admin:
        results["found_in"].append("admin_users")
        results["details"]["admin_users"] = {
            "mfa_enabled": user_in_admin.get('mfa_enabled'),
            "has_mfa_secret": 'mfa_secret' in user_in_admin,
            "mfa_verified_at": user_in_admin.get('mfa_verified_at'),
            "mfa_created_at": user_in_admin.get('mfa_created_at')
        }
        print(f"   - mfa_enabled: {user_in_admin.get('mfa_enabled')}")
        print(f"   - mfa_secret: {'SÍ' if user_in_admin.get('mfa_secret') else 'NO'}")
    
    # Buscar en Adm_Users
    try:
        user_in_adm_users = await Database.adm_users.find_one({"_id": user_id})
        print(f"🔍 En colección 'Adm_Users': {user_in_adm_users is not None}")
        if user_in_adm_users:
            results["found_in"].append("Adm_Users")
            results["details"]["Adm_Users"] = {
                "mfa_enabled": user_in_adm_users.get('mfa_enabled'),
                "has_mfa_secret": 'mfa_secret' in user_in_adm_users,
                "mfa_verified_at": user_in_adm_users.get('mfa_verified_at'),
                "mfa_created_at": user_in_adm_users.get('mfa_created_at')
            }
            print(f"   - mfa_enabled: {user_in_adm_users.get('mfa_enabled')}")
            print(f"   - mfa_secret: {'SÍ' if user_in_adm_users.get('mfa_secret') else 'NO'}")
    except Exception as e:
        print(f"⚠️  Error buscando en Adm_Users: {e}")
    
    # También buscar por ObjectId si es posible
    try:
        oid = ObjectId(user_id)
        user_in_users_oid = await Database.users.find_one({"_id": oid})
        if user_in_users_oid:
            print(f"🔍 En colección 'users' (con ObjectId): True")
            if "users" not in results["found_in"]:
                results["found_in"].append("users_oid")
                results["details"]["users_oid"] = {
                    "mfa_enabled": user_in_users_oid.get('mfa_enabled'),
                    "has_mfa_secret": 'mfa_secret' in user_in_users_oid
                }
    except:
        print("🔍 No se pudo convertir a ObjectId")
    
    return {
        "ok": True,
        **results
    }

@router.post("/debug/mfa/{user_id}/disable")
async def debug_disable_mfa(user_id: str):
    """Desactivar MFA en todas las colecciones (debug)"""
    print(f"🔧 DESACTIVANDO MFA para user_id={user_id}")
    
    results = []
    
    # Intentar en users
    result_users = await Database.users.update_one(
        {"_id": user_id},
        {"$set": {"mfa_enabled": False}}
    )
    results.append({
        "collection": "users",
        "modified": result_users.modified_count,
        "matched": result_users.matched_count
    })
    print(f"📝 Users modificados: {result_users.modified_count}")
    
    # Intentar en Adm_Users (si existe)
    try:
        result_adm = await Database.adm_users.update_one(
            {"_id": user_id},
            {"$set": {"mfa_enabled": False}}
        )
        results.append({
            "collection": "Adm_Users",
            "modified": result_adm.modified_count,
            "matched": result_adm.matched_count
        })
        print(f"📝 Adm_Users modificados: {result_adm.modified_count}")
    except Exception as e:
        print(f"⚠️  No se pudo actualizar Adm_Users: {e}")
    
    # Intentar en admin_users
    result_admin = await Database.admin_users.update_one(
        {"_id": user_id},
        {"$set": {"mfa_enabled": False}}
    )
    results.append({
        "collection": "admin_users",
        "modified": result_admin.modified_count,
        "matched": result_admin.matched_count
    })
    print(f"📝 Admin users modificados: {result_admin.modified_count}")
    
    return {
        "ok": True,
        "message": "MFA desactivado en todas las colecciones",
        "results": results
    }
