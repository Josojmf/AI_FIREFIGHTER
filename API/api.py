"""
FirefighterAI - FastAPI API MODULAR COMPLETO
===========================================
Arquitectura modular con 7 routers separados
"""

import os
import warnings
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from uuid import uuid4
import bcrypt
import jwt
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn

# MongoDB
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

# Cache
from simple_memory_cache import get_cache_stats, clear_cache

load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

MONGO_USER = os.getenv("MONGO_USER", "joso")
MONGO_PASS = os.getenv("MONGO_PASS", "XyGItdDKpWkfJfjT")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.yzzh9ig.mongodb.net")
DB_NAME = os.getenv("DB_NAME", "FIREFIGHTER")
JWT_SECRET = os.getenv("SECRET_KEY", "firefighter-secret-key-2024")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

def get_mongo_uri():
    if MONGO_USER and MONGO_PASS:
        return f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority"
    return "mongodb://localhost:27017"

# ============================================================================
# DATABASE (Global para que lo importen los routers)
# ============================================================================

class DB:
    client: Optional[AsyncIOMotorClient] = None
    users = None
    admin_users = None
    access_tokens = None
    memory_cards = None
    resets = None

db = DB()

# ============================================================================
# UTILS (Para que los routers los importen)
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

def serialize_doc(doc):
    """Serializar documento MongoDB"""
    if "_id" in doc:
        if isinstance(doc["_id"], ObjectId):
            doc["id"] = str(doc["_id"])
        else:
            doc["id"] = doc["_id"]
        del doc["_id"]
    return doc

# ============================================================================
# AUTH DEPENDENCY (Para que los routers lo importen)
# ============================================================================

security = HTTPBearer()

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
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
# LIFESPAN
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=" * 60)
    print("🚀 FirefighterAI API - MODULAR COMPLETO")
    print("=" * 60)
    
    try:
        db.client = AsyncIOMotorClient(get_mongo_uri())
        await db.client.admin.command('ping')
        
        database = db.client[DB_NAME]
        db.users = database["users"]
        db.admin_users = database["Adm_Users"]
        db.access_tokens = database["access_tokens"]
        db.memory_cards = database["memory_cards"]
        db.resets = database["password_resets"]
        
        print("✅ Conectado a MongoDB")
    except Exception as e:
        print(f"❌ Error MongoDB: {e}")
    
    yield
    
    # Shutdown
    if db.client:
        db.client.close()
    print("🔒 API cerrada")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="FirefighterAI API",
    version="2.0.0-modular-complete",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# IMPORTAR Y REGISTRAR ROUTERS
# ============================================================================

routers_loaded = []

# 1. AUTH Router
try:
    from routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/api", tags=["Authentication"])
    routers_loaded.append("✅ Auth (5 endpoints)")
    print("✅ Router Auth registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Auth: {e}")

# 2. USERS Router
try:
    from routes.users import router as users_router
    app.include_router(users_router, prefix="/api", tags=["Users"])
    routers_loaded.append("✅ Users (6 endpoints)")
    print("✅ Router Users registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Users: {e}")

# 3. MEMORY CARDS Router
try:
    from routes.memory_cards import router as cards_router
    app.include_router(cards_router, prefix="/api", tags=["Memory Cards"])
    routers_loaded.append("✅ Memory Cards (9 endpoints)")
    print("✅ Router Memory Cards registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Memory Cards: {e}")

# 4. ACCESS TOKENS Router
try:
    from routes.access_tokens import router as tokens_router
    app.include_router(tokens_router, prefix="/api", tags=["Access Tokens"])
    routers_loaded.append("✅ Access Tokens (8 endpoints)")
    print("✅ Router Access Tokens registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Access Tokens: {e}")

# 5. DOCKER Router
try:
    from routes.docker import router as docker_router
    app.include_router(docker_router, prefix="/api", tags=["Docker"])
    routers_loaded.append("✅ Docker (6 endpoints)")
    print("✅ Router Docker registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Docker: {e}")

# 6. ADMIN Router
try:
    from routes.admin import router as admin_router
    app.include_router(admin_router, prefix="/api", tags=["Admin"])
    routers_loaded.append("✅ Admin (7 endpoints)")
    print("✅ Router Admin registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Admin: {e}")

# 7. HEALTH Router
try:
    from routes.health import router as health_router
    app.include_router(health_router, prefix="/api", tags=["Health"])
    routers_loaded.append("✅ Health (5 endpoints)")
    print("✅ Router Health registrado")
except Exception as e:
    print(f"❌ No se pudo cargar router Health: {e}")

print("=" * 60)
print(f"📦 Routers cargados: {len(routers_loaded)}/7")
print("=" * 60)

# 8. RUNTIME CONFIG Router
try:
    from routes.runtime_config import router as runtime_config_router
    app.include_router(runtime_config_router, tags=["Runtime Config"])
    print("✅ Router Runtime Config registrado")
except Exception as e:
    print(f"❌ No se pudo cargar Runtime Config: {e}")


# ============================================================================
# ENDPOINTS GENERALES
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "version": "2.0.0-modular-complete",
        "docs": "/docs",
        "redoc": "/redoc",
        "architecture": "modular",
        "routers": routers_loaded,
        "total_routers": len(routers_loaded)
    }

@app.get("/api/health")
async def health_basic():
    """Health check básico (sin auth)"""
    try:
        # Contar usuarios
        users_count = await db.users.count_documents({})
        
        return {
            "ok": True,
            "status": "healthy",
            "database": "connected",
            "users_count": users_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "ok": False,
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import multiprocessing
    import sys
    import platform
    
    warnings.filterwarnings('ignore', category=DeprecationWarning)
    
    os_name = platform.system()
    is_windows = os_name == "Windows"
    
    print("=" * 60)
    print("🚀 FirefighterAI FastAPI - MODULAR COMPLETO")
    print("=" * 60)
    print(f"💻 Sistema: {os_name}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print("🌐 Servidor: http://0.0.0.0:5000")
    print("📦 Arquitectura: Modular (7 routers)")
    print("📚 Docs: http://localhost:5000/docs")
    print("=" * 60)
    
    if is_windows:
        multiprocessing.freeze_support()
        
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=5000,
            reload=True,
            workers=1,
            log_level="info"
        )
    else:
        uvicorn.run(
            "api:app",
            host="0.0.0.0",
            port=5000,
            workers=4,
            log_level="info"
        )