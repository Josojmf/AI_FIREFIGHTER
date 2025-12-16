"""
Routes Package - API Routers
============================
"""

from .auth import router as auth_router
from .users import router as users_router
from .memory_cards import router as memory_cards_router
from .access_tokens import router as access_tokens_router
from .docker import router as docker_router
from .admin import router as admin_router
from .health import router as health_router


__all__ = [
    "auth_router",
    "users_router",
    "memory_cards_router",
    "access_tokens_router",
    "docker_router",
    "admin_router",
    "health_router",
]