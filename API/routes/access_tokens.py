"""
Access Tokens Routes - Token management endpoints
================================================
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from bson import ObjectId
from uuid import uuid4
import secrets
from utils.jwt_utils import make_jwt, decode_jwt


from models.token_models import (
    AccessTokenCreate,
    AccessTokenUpdate,
    AccessTokenResponse,
    AccessTokenUse
)
from dependencies.auth import require_user, require_admin
from database import Database
from services.email_service import send_token_email


router = APIRouter(tags=["access-tokens"])
db = Database()


def safe_datetime(dt):
    """Helper para manejar fechas"""
    if isinstance(dt, datetime):
        return dt
    return None


async def validate_access_token(token_value: str) -> tuple[bool, str]:
    """Validar si un token de acceso es válido"""
    token = await db.access_tokens.find_one({"token": token_value})
    
    if not token:
        return False, "Token no encontrado"
    
    if token["status"] != "active":
        return False, f"Token {token['status']}"
    
    if token["current_uses"] >= token["max_uses"]:
        return False, "Token agotado"
    
    if token.get("expires_at"):
        if datetime.utcnow() > token["expires_at"]:
            await db.access_tokens.update_one(
                {"token": token_value},
                {"$set": {"status": "expired"}}
            )
            return False, "Token expirado"
    
    return True, "Token válido"


@router.get("/access_tokens")
async def list_access_tokens(admin_data: Dict = Depends(require_admin)):
    """Listar todos los access tokens (solo admin)"""
    try:
        tokens_cursor = db.access_tokens.find({}).sort("created_at", -1)
        tokens_list = await tokens_cursor.to_list(length=100)

        result = []

        for token in tokens_list:
            created_at = safe_datetime(token.get("created_at"))
            expires_at = safe_datetime(token.get("expires_at"))
            last_used_at = safe_datetime(token.get("last_used_at"))

            current_uses = token.get("current_uses", 0)
            max_uses = token.get("max_uses", 1)

            # Estado calculado
            if token.get("status") != "active":
                computed_status = token["status"]
            elif expires_at and expires_at < datetime.utcnow():
                computed_status = "expired"
            elif current_uses >= max_uses:
                computed_status = "exhausted"
            else:
                computed_status = "active"

            result.append({
                "id": str(token["_id"]),
                "token": token.get("token"),
                "name": token.get("name"),
                "status": token.get("status", "active"),
                "computed_status": computed_status,
                "current_uses": current_uses,
                "max_uses": max_uses,
                "usage_percentage": (current_uses / max_uses) * 100 if max_uses > 0 else 100,
                "created_by": token.get("created_by"),
                "created_at": created_at.isoformat() if created_at else None,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "last_used_at": last_used_at.isoformat() if last_used_at else None,
            })

        return {
            "ok": True,
            "tokens": result,
            "total": len(result)
        }

    except Exception as e:
        print(f"❌ Error obteniendo tokens: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo tokens")


@router.post("/access_tokens")
async def create_access_token(
    request: AccessTokenCreate, 
    admin_data: Dict = Depends(require_admin)
):
    """Crear nuevo access token (solo admin)"""
    try:
        # Generar token único
        token_value = secrets.token_urlsafe(64)
        
        # Crear documento
        token_doc = {
            "_id": str(uuid4()),
            "token": token_value,
            "name": request.name,
            "max_uses": request.max_uses,
            "current_uses": 0,
            "status": "active",
            "created_at": datetime.utcnow(),
            "created_by": admin_data["username"],
            "expires_at": request.expires_at,
            "usage_history": [],
            "metadata": request.metadata
        }
        
        # Enviar email si se especifica
        if request.send_email and request.recipient_email:
            token_doc["email_sent_to"] = request.recipient_email
            token_doc["email_sent_at"] = datetime.utcnow()
            
            try:
                email_sent = send_token_email(
                    recipient_email=request.recipient_email,
                    token_name=request.name,
                    token_value=token_value,
                    max_uses=request.max_uses,
                    expires_at=request.expires_at.isoformat() if request.expires_at else None,
                    created_by=admin_data["username"]
                )
                token_doc["email_status"] = "sent" if email_sent else "failed"
                print(f"📧 Email enviado a {request.recipient_email}")
            except Exception as e:
                print(f"⚠️ Error enviando email: {e}")
                token_doc["email_status"] = "failed"
                token_doc["email_error"] = str(e)
        
        await db.access_tokens.insert_one(token_doc)
        
        # Remove _id for response
        token_doc['id'] = token_doc.pop('_id')
        
        return {
            "ok": True,
            "token": token_doc,
            "detail": "Token creado exitosamente",
            "token_value": token_value  # Solo en respuesta de creación
        }
        
    except Exception as e:
        print(f"❌ Error creando token: {e}")
        raise HTTPException(status_code=500, detail="Error creando token")


@router.get("/access_tokens/stats")
async def get_access_tokens_stats(admin_data: Dict = Depends(require_admin)):
    """Obtener estadísticas de tokens (solo admin)"""
    try:
        total = await db.access_tokens.count_documents({})
        active = await db.access_tokens.count_documents({"status": "active"})
        expired = await db.access_tokens.count_documents({"status": "expired"})
        
        # Calcular exhausted (usos completos)
        all_tokens = await db.access_tokens.find({}).to_list(length=1000)
        exhausted = sum(1 for t in all_tokens if t.get("current_uses", 0) >= t.get("max_uses", 1))
        
        # Total usos
        total_uses = sum(t.get("current_uses", 0) for t in all_tokens)

        return {
            "ok": True,
            "stats": {
                "total_tokens": total,
                "active_tokens": active,
                "expired_tokens": expired,
                "exhausted_tokens": exhausted,
                "total_uses": total_uses
            }
        }
    except Exception as e:
        print(f"❌ Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@router.get("/access_tokens/{token_value}/validate")
async def validate_token_public(token_value: str):
    """Validar token público (sin auth requerida)"""
    try:
        valid, message = await validate_access_token(token_value)
        
        # Info adicional si es válido
        additional_info = {}
        if valid:
            token_doc = await db.access_tokens.find_one({"token": token_value})
            if token_doc:
                additional_info = {
                    "name": token_doc.get("name"),
                    "current_uses": token_doc.get("current_uses", 0),
                    "max_uses": token_doc.get("max_uses", 1),
                    "expires_at": token_doc.get("expires_at").isoformat() if token_doc.get("expires_at") else None
                }
        
        return {
            "ok": valid,
            "valid": valid,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            **additional_info
        }
        
    except Exception as e:
        return {
            "ok": False, 
            "valid": False, 
            "message": f"Error: {e}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/access_tokens/{token_id}")
async def get_access_token_by_id(token_id: str, admin_data: Dict = Depends(require_admin)):
    """Obtener detalles de token por ID (solo admin)"""
    try:
        try:
            oid = ObjectId(token_id)
        except:
            oid = token_id
        
        token = await db.access_tokens.find_one({"_id": oid})
        
        if not token:
            raise HTTPException(status_code=404, detail="Token no encontrado")
        
        token['id'] = str(token['_id'])
        token.pop('_id', None)
        
        # Format dates
        if token.get('created_at'):
            token['created_at'] = token['created_at'].isoformat()
        if token.get('expires_at'):
            token['expires_at'] = token['expires_at'].isoformat()
        if token.get('last_used_at'):
            token['last_used_at'] = token['last_used_at'].isoformat()
        
        return {"ok": True, "token": token}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo token: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo token")


@router.put("/access_tokens/{token_id}")
async def update_access_token(
    token_id: str,
    updates: AccessTokenUpdate,
    admin_data: Dict = Depends(require_admin)
):
    """Actualizar access token (solo admin)"""
    try:
        try:
            oid = ObjectId(token_id)
        except:
            oid = token_id
        
        # Preparar updates
        update_doc = {"$set": {}}
        
        if updates.name is not None:
            update_doc["$set"]["name"] = updates.name
        if updates.max_uses is not None:
            update_doc["$set"]["max_uses"] = updates.max_uses
        if updates.expires_at is not None:
            update_doc["$set"]["expires_at"] = updates.expires_at
        if updates.status is not None:
            update_doc["$set"]["status"] = updates.status
        if updates.metadata is not None:
            update_doc["$set"]["metadata"] = updates.metadata
        
        if not update_doc["$set"]:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        result = await db.access_tokens.update_one(
            {"_id": oid},
            update_doc
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Token no encontrado")
        
        return {"ok": True, "detail": "Token actualizado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando token: {e}")
        raise HTTPException(status_code=500, detail="Error actualizando token")


@router.delete("/access_tokens/{token_id}")
async def delete_access_token(
    token_id: str,
    admin_data: Dict = Depends(require_admin)
):
    """Eliminar access token (solo admin)"""
    try:
        try:
            oid = ObjectId(token_id)
        except:
            oid = token_id
        
        result = await db.access_tokens.delete_one({"_id": oid})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Token no encontrado")
        
        return {"ok": True, "detail": "Token eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando token: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando token")


@router.post("/access_tokens/{token_value}/use")
async def use_access_token(
    token_value: str,
    user_info: AccessTokenUse = Body(default=AccessTokenUse())
):
    """Usar/consumir access token (público)"""
    try:
        # Validar token
        valid, message = await validate_access_token(token_value)
        if not valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Incrementar uso
        usage_entry = {
            "used_at": datetime.utcnow(),
            "used_by": user_info.username or "unknown",
            "ip_address": user_info.ip or "unknown",
            "user_agent": user_info.user_agent or "unknown"
        }
        
        result = await db.access_tokens.update_one(
            {"token": token_value},
            {
                "$inc": {"current_uses": 1},
                "$set": {"last_used_at": datetime.utcnow()},
                "$push": {"usage_history": usage_entry}
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="No se pudo registrar el uso")
        
        return {
            "ok": True,
            "detail": "Token usado exitosamente",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error usando token: {e}")
        raise HTTPException(status_code=500, detail="Error usando token")