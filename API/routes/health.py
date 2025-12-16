"""
Health Routes - Health checks and monitoring endpoints
=====================================================
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from datetime import datetime
import psutil

from dependencies.auth import require_admin
from database import Database
from simple_memory_cache import get_cache_stats


router = APIRouter(tags=["health"])
db = Database()


@router.get("/health")
async def health_check():
    """Health check básico"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0-modular"
    }


@router.get("/health/detailed")
async def detailed_health_check(admin_data: Dict = Depends(require_admin)):
    """Health check detallado (solo admin)"""
    try:
        # MongoDB health
        mongo_healthy = False
        try:
            await db.client.admin.command('ping')
            mongo_healthy = True
        except:
            pass
        
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Cache stats
        cache = get_cache_stats()
        
        return {
            "ok": True,
            "status": "healthy" if mongo_healthy else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0-modular",
            "services": {
                "mongodb": {
                    "status": "healthy" if mongo_healthy else "unhealthy",
                    "database": db.db.name if db.db else "N/A"
                },
                "cache": {
                    "status": "healthy",
                    "entries": cache.get("total_entries", 0),
                    "usage": f"{cache.get('usage_percent', 0)}%"
                }
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            }
        }
        
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return {
            "ok": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/health/db")
async def database_health_check():
    """Health check de MongoDB"""
    try:
        # Ping MongoDB
        await db.client.admin.command('ping')
        
        # Contar documentos en colecciones principales
        users_count = await db.users.count_documents({})
        cards_count = await db.memory_cards.count_documents({})
        tokens_count = await db.access_tokens.count_documents({})
        
        return {
            "ok": True,
            "status": "healthy",
            "database": db.db.name,
            "collections": {
                "users": users_count,
                "memory_cards": cards_count,
                "access_tokens": tokens_count
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error en DB health check: {e}")
        return {
            "ok": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/logs")
async def get_logs(
    lines: int = 100,
    admin_data: Dict = Depends(require_admin)
):
    """Obtener logs del sistema (solo admin)"""
    try:
        # TODO: Implementar lectura de logs
        # Por ahora retorna ejemplo
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "API funcionando correctamente"
            }
        ]
        
        return {
            "ok": True,
            "logs": logs,
            "count": len(logs)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo logs")


@router.get("/cache/stats")
async def cache_stats():
    """Estadísticas del cache en memoria"""
    return {"ok": True, "stats": get_cache_stats()}