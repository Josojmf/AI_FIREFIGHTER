"""
User Routes - User management endpoints
=======================================
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from bson.errors import InvalidId

from models.user_models import UserUpdate, UserResponse, UserListResponse
from dependencies.auth import require_user, require_admin
from simple_memory_cache import cache_user_data
from database import Database


router = APIRouter(tags=["users"])
db = Database()


@router.get("/users", response_model=Dict[str, Any])
async def list_users(admin_data: Dict = Depends(require_admin)):
    """Listar todos los usuarios (solo admin)"""
    try:
        users_cursor = db.users.find({}, {
            'password_hash': 0,
            'mfa_secret': 0
        })
        
        users_list = await users_cursor.to_list(length=1000)
        
        # Add computed fields
        for user in users_list:
            if isinstance(user.get('_id'), ObjectId):
                user['id'] = str(user['_id'])
                del user['_id']

            user['has_leitner_progress'] = bool(
                user.get('leitner_system', {}).get('total_cards', 0)
            )
            user['has_backoffice_cards'] = user.get('role') == 'admin'

        return {'ok': True, 'users': users_list}
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo usuarios")


@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user(user_id: str, user_data: Dict = Depends(require_user)):
    """Obtener detalle de usuario"""
    try:
        # Solo admin o el propio usuario
        if user_data.get('role') != 'admin' and user_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
        user = await db.users.find_one({"_id": oid})
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Remove sensitive data
        user.pop('password_hash', None)
        user.pop('mfa_secret', None)
        user['id'] = str(user['_id']) if isinstance(user['_id'], ObjectId) else user['_id']
        user.pop('_id', None)
        
        return {"ok": True, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo usuario: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo usuario")


@router.get("/users/{user_id}/progress", response_model=Dict[str, Any])
@cache_user_data(ttl=120)
async def get_user_progress(user_id: str, user_data: Dict = Depends(require_user)):
    """Obtener progreso Leitner del usuario"""
    try:
        # Solo admin o el propio usuario
        if user_data.get('role') != 'admin' and user_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
        user = await db.users.find_one({"_id": oid})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        leitner = user.get('leitner_system', {})
        boxes = leitner.get('boxes', {})
        
        progress = {
            "total_cards": sum(len(cards) for cards in boxes.values()),
            "boxes": {k: len(v) for k, v in boxes.items()},
            "last_study": leitner.get('last_study'),
            "created_at": leitner.get('created_at'),
            "study_sessions": leitner.get('study_sessions', 0),
            "streak": leitner.get('streak', 0)
        }
        
        return {"ok": True, "progress": progress}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo progreso: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo progreso")


@router.put("/users/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: str,
    updates: UserUpdate,
    user_data: Dict = Depends(require_user)
):
    """Actualizar usuario"""
    try:
        # Solo admin o el propio usuario
        if user_data.get('role') != 'admin' and user_data.get('user_id') != user_id:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
        # Preparar updates
        update_doc = {"$set": {"updated_at": datetime.utcnow()}}
        
        if updates.email is not None:
            update_doc["$set"]["email"] = updates.email
        if updates.name is not None:
            update_doc["$set"]["name"] = updates.name
        if updates.role is not None and user_data.get('role') == 'admin':
            # Solo admin puede cambiar roles
            update_doc["$set"]["role"] = updates.role
        if updates.mfa_enabled is not None:
            update_doc["$set"]["mfa_enabled"] = updates.mfa_enabled
        
        # Actualizar
        result = await db.users.update_one(
            {"_id": oid},
            update_doc
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No se pudo actualizar")
        
        return {"ok": True, "detail": "Usuario actualizado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando usuario: {e}")
        raise HTTPException(status_code=500, detail="Error actualizando usuario")


@router.delete("/users/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: str,
    admin_data: Dict = Depends(require_admin)
):
    """Eliminar usuario (solo admin)"""
    try:
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
        # No permitir que el admin se elimine a sí mismo
        if admin_data.get('user_id') == user_id:
            raise HTTPException(
                status_code=400,
                detail="No puedes eliminar tu propia cuenta"
            )
        
        result = await db.users.delete_one({"_id": oid})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"ok": True, "detail": "Usuario eliminado exitosamente"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando usuario: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando usuario")


@router.get("/users/me", response_model=Dict[str, Any])
async def get_current_user(user_data: Dict = Depends(require_user)):
    """Obtener información del usuario actual"""
    try:
        user_id = user_data.get('user_id')
        
        try:
            oid = ObjectId(user_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID de usuario inválido")
        
        user = await db.users.find_one({"_id": oid})
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Remove sensitive data
        user.pop('password_hash', None)
        user.pop('mfa_secret', None)
        user['id'] = str(user['_id']) if isinstance(user['_id'], ObjectId) else user['_id']
        user.pop('_id', None)
        
        return {"ok": True, "user": user}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo usuario actual: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo usuario actual")