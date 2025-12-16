"""
Admin Routes - Dashboard and admin endpoints
===========================================
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime, timedelta

from dependencies.auth import require_admin
from database import Database
from simple_memory_cache import clear_cache


router = APIRouter(tags=["admin"])
db = Database()


@router.get("/dashboard/stats")
async def get_dashboard_stats(admin_data: Dict = Depends(require_admin)):
    """Estadísticas generales del dashboard (solo admin)"""
    try:
        # Usuarios
        total_users = await db.users.count_documents({})
        active_users = await db.users.count_documents({"status": "active"})
        
        # Memory Cards
        total_cards = await db.memory_cards.count_documents({})
        
        # Access Tokens
        total_tokens = await db.access_tokens.count_documents({})
        active_tokens = await db.access_tokens.count_documents({"status": "active"})
        
        # Actividad reciente (últimos 7 días)
        week_ago = datetime.utcnow() - timedelta(days=7)
        new_users_week = await db.users.count_documents({
            "created_at": {"$gte": week_ago}
        })
        new_cards_week = await db.memory_cards.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        return {
            "ok": True,
            "stats": {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "new_this_week": new_users_week
                },
                "memory_cards": {
                    "total": total_cards,
                    "new_this_week": new_cards_week
                },
                "access_tokens": {
                    "total": total_tokens,
                    "active": active_tokens
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@router.get("/admin/users/stats")
async def get_users_stats(admin_data: Dict = Depends(require_admin)):
    """Estadísticas detalladas de usuarios (solo admin)"""
    try:
        total = await db.users.count_documents({})
        active = await db.users.count_documents({"status": "active"})
        with_mfa = await db.users.count_documents({"mfa_enabled": True})
        
        # Por rol
        admins = await db.users.count_documents({"role": "admin"})
        regular_users = await db.users.count_documents({"role": "user"})
        
        # Registros recientes
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        registered_today = await db.users.count_documents({
            "created_at": {"$gte": today}
        })
        
        week_ago = datetime.utcnow() - timedelta(days=7)
        registered_week = await db.users.count_documents({
            "created_at": {"$gte": week_ago}
        })
        
        return {
            "ok": True,
            "stats": {
                "total": total,
                "active": active,
                "inactive": total - active,
                "with_mfa": with_mfa,
                "by_role": {
                    "admin": admins,
                    "user": regular_users
                },
                "registrations": {
                    "today": registered_today,
                    "this_week": registered_week
                }
            }
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo user stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@router.get("/admin/cards/stats")
async def get_cards_stats(admin_data: Dict = Depends(require_admin)):
    """Estadísticas detalladas de memory cards (solo admin)"""
    try:
        cards = await db.memory_cards.find({}).to_list(length=10000)
        
        total = len(cards)
        by_box = {}
        by_category = {}
        by_difficulty = {}
        total_reviews = 0
        
        for card in cards:
            # By box
            box = str(card.get("box", 1))
            by_box[box] = by_box.get(box, 0) + 1
            
            # By category
            category = card.get("category", "General")
            by_category[category] = by_category.get(category, 0) + 1
            
            # By difficulty
            difficulty = card.get("difficulty", "medium")
            by_difficulty[difficulty] = by_difficulty.get(difficulty, 0) + 1
            
            # Reviews
            total_reviews += card.get("times_reviewed", 0)
        
        return {
            "ok": True,
            "stats": {
                "total": total,
                "by_box": by_box,
                "by_category": by_category,
                "by_difficulty": by_difficulty,
                "total_reviews": total_reviews,
                "avg_reviews_per_card": round(total_reviews / total, 2) if total > 0 else 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo cards stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@router.get("/admin/tokens/stats")
async def get_tokens_stats(admin_data: Dict = Depends(require_admin)):
    """Estadísticas detalladas de access tokens (solo admin)"""
    try:
        tokens = await db.access_tokens.find({}).to_list(length=1000)
        
        total = len(tokens)
        active = sum(1 for t in tokens if t.get("status") == "active")
        expired = sum(1 for t in tokens if t.get("status") == "expired")
        exhausted = sum(1 for t in tokens if t.get("current_uses", 0) >= t.get("max_uses", 1))
        
        total_uses = sum(t.get("current_uses", 0) for t in tokens)
        total_max_uses = sum(t.get("max_uses", 1) for t in tokens)
        
        return {
            "ok": True,
            "stats": {
                "total": total,
                "active": active,
                "expired": expired,
                "exhausted": exhausted,
                "total_uses": total_uses,
                "total_max_uses": total_max_uses,
                "usage_rate": round((total_uses / total_max_uses * 100), 2) if total_max_uses > 0 else 0
            }
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo tokens stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")


@router.post("/admin/cache/clear")
async def clear_system_cache(admin_data: Dict = Depends(require_admin)):
    """Limpiar cache del sistema (solo admin)"""
    try:
        clear_cache()
        return {
            "ok": True,
            "detail": "Cache limpiado exitosamente"
        }
    except Exception as e:
        print(f"❌ Error limpiando cache: {e}")
        raise HTTPException(status_code=500, detail="Error limpiando cache")


@router.post("/admin/system/backup")
async def create_system_backup(admin_data: Dict = Depends(require_admin)):
    """Crear backup del sistema (solo admin)"""
    try:
        # TODO: Implementar backup real
        return {
            "ok": True,
            "detail": "Backup functionality not implemented yet",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        print(f"❌ Error creando backup: {e}")
        raise HTTPException(status_code=500, detail="Error creando backup")