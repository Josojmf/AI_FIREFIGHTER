"""
FirefighterAI - FastAPI API CORREGIDO COMPLETO
=============================================
Solucionando importaciones circulares
"""

import os
import warnings
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from uuid import uuid4
import bcrypt
import jwt
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import uvicorn
from bson import ObjectId
from dotenv import load_dotenv

# Importar Database
from database import Database

load_dotenv()

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "firefighter-super-secret-jwt-key-2024")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# ============================================================================
# INSTANCIA DATABASE - CREAR AQUÍ PARA EVITAR IMPORTACIÓN CIRCULAR
# ============================================================================
db = Database()

# ============================================================================
# UTILS GLOBALES
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
# AUTH DEPENDENCIES (Solo aquí, NO duplicar)
# ============================================================================

security = HTTPBearer()

async def require_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    token = credentials.credentials
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    username = payload.get("username")
    
    # Buscar usuario usando instancia db
    user = await db.users.find_one({"username": username})
    if not user:
        user = await db.admin_users.find_one({"username": username})
    
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    
    return {
        "username": username,
        "role": user.get("role", "user"),
        "user_id": str(user["_id"]) if "_id" in user else user.get("id", "")
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
    print("🚀 FirefighterAI API - CORREGIDO")
    print("=" * 60)
    
    try:
        # Conectar a MongoDB usando Database
        await Database.connect_db()
        print("✅ Conectado a MongoDB usando Database")
        
    except Exception as e:
        print(f"❌ Error MongoDB: {e}")
        import traceback
        traceback.print_exc()
    
    yield
    
    # Shutdown - Desconectar de MongoDB
    await Database.close_db()
    print("🔒 API cerrada y MongoDB desconectado")

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="FirefighterAI API",
    version="2.0.0-fixed",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# ============================================================================
# MIDDLEWARE
# ============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de debug
@app.middleware("http")
async def debug_middleware(request: Request, call_next):
    print(f"🔍 DEBUG: {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"🔍 DEBUG Response Status: {response.status_code}")
    return response

# ============================================================================
# IMPORTAR ROUTERS DESPUÉS DE DEFINIR APP - EVITA IMPORTACIÓN CIRCULAR
# ============================================================================

# SOLO IMPORTAR LOS QUE EXISTEN
try:
    from routes.users import router as users_router
    app.include_router(users_router, prefix="/api", tags=["users"])
    print("✅ Users router montado")
except ImportError as e:
    print(f"⚠️ Users router no disponible: {e}")

try:
    from routes.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    print("✅ Auth router montado")
except ImportError as e:
    print(f"⚠️ Auth router no disponible: {e}")

try:
    from routes.memory_cards import router as memory_cards_router
    app.include_router(memory_cards_router, prefix="/api", tags=["memory-cards"])
    print("✅ Memory cards router montado")
except ImportError as e:
    print(f"⚠️ Memory cards router no disponible: {e}")

try:
    from routes.health import router as health_router
    app.include_router(health_router, prefix="/api", tags=["health"])
    print("✅ Health router montado")
except ImportError as e:
    print(f"⚠️ Health router no disponible: {e}")

try:
    from routes.admin import router as admin_router
    app.include_router(admin_router, prefix="/api", tags=["admin"])
    print("✅ Admin router montado")
except ImportError as e:
    print(f"⚠️ Admin router no disponible: {e}")

try:
    from routes.access_tokens import router as access_tokens_router
    app.include_router(access_tokens_router, prefix="/api", tags=["access-tokens"])
    print("✅ Access tokens router montado")
except ImportError as e:
    print(f"⚠️ Access tokens router no disponible: {e}")

try:
    from routes.docker import router as docker_router
    app.include_router(docker_router, prefix="/api", tags=["docker"])
    print("✅ Docker router montado")
except ImportError as e:
    print(f"⚠️ Docker router no disponible: {e}")

# ============================================================================
# ENDPOINTS CRÍTICOS PARA BACKOFFICE (Compatibilidad)
# ============================================================================

@app.post("/api/login")
async def api_login_compat(request: Dict[str, Any]):
    """Endpoint de compatibilidad para /api/login"""
    try:
        # Validar request básico
        username = request.get("username", "").strip()
        password = request.get("password", "").strip()
        mfa_token = request.get("mfa_token", "").strip()
        
        print(f"🔐 Login attempt for: {username}")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username y password requeridos")
        
        # Verificar que la base de datos esté conectada
        if not db.is_connected():
            await db.ensure_connection()
        
        # Buscar usuario usando instancia db
        query = {"$or": [
            {"username": username},
            {"email": username}
        ]}
        
        user_doc = await db.users.find_one(query)
        if not user_doc:
            user_doc = await db.admin_users.find_one(query)
        
        if not user_doc:
            print(f"❌ User not found: {username}")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Verificar contraseña
        password_field = "password_hash" if "password_hash" in user_doc else "password"
        if not verify_password(password, user_doc[password_field]):
            print(f"❌ Wrong password for: {username}")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        # Verificar estado
        if user_doc.get("status") != "active":
            raise HTTPException(status_code=401, detail="Cuenta desactivada")
        
        # Verificar MFA si está habilitado
        if user_doc.get("mfa_enabled", False):
            if not mfa_token:
                raise HTTPException(status_code=401, detail="MFA token requerido")
            
            # Aquí iría la validación del MFA token
            # Por ahora asumimos que cualquier token de 6 dígitos es válido
            if not (mfa_token.isdigit() and len(mfa_token) == 6):
                raise HTTPException(status_code=401, detail="MFA token inválido")
        
        # Actualizar último login
        if user_doc.get("role") == "admin":
            await db.admin_users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        else:
            await db.users.update_one(
                {"_id": user_doc["_id"]},
                {"$set": {"last_login": datetime.utcnow()}}
            )
        
        # Crear token
        token_payload = {
            "user_id": str(user_doc["_id"]),
            "username": user_doc["username"],
            "role": user_doc.get("role", "user")
        }
        token = make_jwt(token_payload)
        
        print(f"✅ Login successful for: {username}")
        
        return {
            "ok": True,
            "access_token": token,
            "user": {
                "id": str(user_doc["_id"]),
                "username": user_doc["username"],
                "email": user_doc.get("email", ""),
                "role": user_doc.get("role", "user"),
                "mfa_enabled": user_doc.get("mfa_enabled", False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error en login compat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error interno")

@app.get("/api/users")
async def api_get_users_compat(user_data: Dict = Depends(require_user)):
    """Endpoint de compatibilidad para /api/users"""
    try:
        if user_data.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        print(f"🔍 GET /api/users - Admin: {user_data['username']}")
        
        # Obtener usuarios de ambas colecciones usando instancia db
        regular_users = []
        admin_user_list = []
        
        cursor = db.users.find({}, {"password": 0, "password_hash": 0})
        async for user in cursor:
            regular_users.append(serialize_doc(user))
            
        cursor = db.admin_users.find({}, {"password": 0, "password_hash": 0})
        async for user in cursor:
            admin_user_list.append(serialize_doc(user))
        
        all_users = regular_users + admin_user_list
        
        print(f"✅ Obtenidos {len(all_users)} usuarios")
        
        return {
            "ok": True,
            "users": all_users,
            "count": len(all_users)
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo usuarios: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.get("/api/memory-cards")
async def api_get_memory_cards_compat(user_data: Dict = Depends(require_user)):
    """Endpoint de compatibilidad para /api/memory-cards"""
    try:
        print(f"🔍 GET /api/memory-cards - Usuario: {user_data['username']}")
        
        # Verificar conexión usando instancia db
        if not db.is_connected():
            await db.ensure_connection()
        
        query = {}
        
        # Si no es admin, solo sus cartas
        if user_data.get('role') != 'admin':
            query["created_by"] = user_data["username"]
        
        print(f"🔍 Buscando cards con query: {query}")
        
        cards_list = []
        cursor = db.memory_cards.find(query)
        async for card in cursor:
            card_data = serialize_doc(card)
            cards_list.append(card_data)
        
        print(f"✅ Encontradas {len(cards_list)} cards para usuario: {user_data['username']}")
        
        return {"ok": True, "cards": cards_list}
        
    except Exception as e:
        print(f"❌ Error obteniendo memory cards: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.post("/api/memory-cards")
async def api_create_memory_card_compat(request: Dict[str, Any], user_data: Dict = Depends(require_user)):
    """Crear memory card"""
    try:
        print(f"🔍 POST /api/memory-cards - Usuario: {user_data['username']}")
        
        # Verificar conexión usando instancia db
        if not db.is_connected():
            await db.ensure_connection()
        
        # Validar datos requeridos
        question = request.get("question", "").strip()
        answer = request.get("answer", "").strip()
        
        if not question or not answer:
            raise HTTPException(status_code=400, detail="Pregunta y respuesta son requeridas")
        
        # Crear memory card
        new_card = {
            "question": question,
            "answer": answer,
            "category": request.get("category", "general"),
            "difficulty": request.get("difficulty", "medium"),
            "tags": request.get("tags", []),
            "created_by": user_data["username"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "box": 1,  # Leitner box inicial
            "review_count": 0,
            "last_reviewed": None,
            "next_review": datetime.utcnow()  # Disponible inmediatamente
        }
        
        result = await db.memory_cards.insert_one(new_card)
        
        if result.inserted_id:
            new_card["id"] = str(result.inserted_id)
            new_card.pop("_id", None)
            print(f"✅ Memory card creada: {result.inserted_id}")
            return {
                "ok": True,
                "card": new_card,
                "message": "Memory card creada exitosamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error creando memory card")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creando memory card: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.get("/api/memory-cards/{card_id}")
async def api_get_memory_card_compat(card_id: str, user_data: Dict = Depends(require_user)):
    """Obtener memory card específica"""
    try:
        print(f"🔍 GET /api/memory-cards/{card_id}")
        
        # Verificar conexión usando instancia db
        if not db.is_connected():
            await db.ensure_connection()
        
        # Buscar card
        try:
            obj_id = ObjectId(card_id)
            card_doc = await db.memory_cards.find_one({"_id": obj_id})
        except:
            obj_id = card_id
            card_doc = await db.memory_cards.find_one({"_id": card_id})
        
        if not card_doc:
            raise HTTPException(status_code=404, detail="Memory card no encontrada")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card_doc.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        card_data = serialize_doc(card_doc)
        
        return {"ok": True, "card": card_data}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error obteniendo memory card: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.put("/api/memory-cards/{card_id}")
async def api_update_memory_card_compat(card_id: str, request: Dict[str, Any], user_data: Dict = Depends(require_user)):
    """Actualizar memory card"""
    try:
        print(f"🔍 PUT /api/memory-cards/{card_id}")
        
        # Verificar conexión usando instancia db
        if not db.is_connected():
            await db.ensure_connection()
        
        # Buscar card
        try:
            obj_id = ObjectId(card_id)
            card_doc = await db.memory_cards.find_one({"_id": obj_id})
        except:
            obj_id = card_id
            card_doc = await db.memory_cards.find_one({"_id": card_id})
        
        if not card_doc:
            raise HTTPException(status_code=404, detail="Memory card no encontrada")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card_doc.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        # Actualizar campos
        update_data = {"updated_at": datetime.utcnow()}
        
        allowed_fields = ["question", "answer", "category", "difficulty", "tags"]
        for field in allowed_fields:
            if field in request:
                update_data[field] = request[field]
        
        result = await db.memory_cards.update_one(
            {"_id": obj_id},
            {"$set": update_data}
        )
        
        if result.modified_count:
            updated_card = await db.memory_cards.find_one({"_id": obj_id})
            print(f"✅ Memory card actualizada: {card_id}")
            return {
                "ok": True,
                "card": serialize_doc(updated_card),
                "message": "Memory card actualizada exitosamente"
            }
        else:
            return {"detail": "Memory card no encontrada"}, 404
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error actualizando memory card: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.delete("/api/memory-cards/{card_id}")
async def api_delete_memory_card_compat(card_id: str, user_data: Dict = Depends(require_user)):
    """Eliminar memory card"""
    try:
        print(f"🔍 DELETE /api/memory-cards/{card_id}")
        
        # Verificar conexión usando instancia db
        if not db.is_connected():
            await db.ensure_connection()
        
        # Buscar card
        try:
            obj_id = ObjectId(card_id)
            card_doc = await db.memory_cards.find_one({"_id": obj_id})
        except:
            obj_id = card_id
            card_doc = await db.memory_cards.find_one({"_id": card_id})
        
        if not card_doc:
            raise HTTPException(status_code=404, detail="Memory card no encontrada")
        
        # Verificar permisos
        if user_data.get('role') != 'admin' and card_doc.get("created_by") != user_data["username"]:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        result = await db.memory_cards.delete_one({"_id": obj_id})
        
        if result.deleted_count:
            print(f"✅ Memory card eliminada: {card_id}")
            return {
                "ok": True,
                "message": "Memory card eliminada exitosamente"
            }
        else:
            return {"detail": "Memory card no encontrada"}, 404
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error eliminando memory card: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@app.get("/api/dashboard/stats")
async def api_dashboard_stats_compat(user_data: Dict = Depends(require_user)):
    """Endpoint de compatibilidad para /api/dashboard/stats"""
    try:
        if user_data.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        print("🔍 Solicitando estadísticas del dashboard...")
        
        # Contar usuarios totales usando instancia db
        total_users = await db.users.count_documents({})
        admin_count = await db.admin_users.count_documents({})
        total_users += admin_count
        
        # Contar usuarios activos (últimos 30 días)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = await db.users.count_documents({
            "last_login": {"$gte": thirty_days_ago}
        })
        
        # Contar memory cards
        total_cards = await db.memory_cards.count_documents({})
        
        # Actividad reciente
        recent_activity = [
            {
                "icon": "👤",
                "text": f"Sistema con {total_users} usuarios registrados",
                "time": "Ahora"
            },
            {
                "icon": "✅",
                "text": f"{active_users} usuarios activos este mes",
                "time": "1 min"
            },
            {
                "icon": "🗃️",
                "text": f"Total de {total_cards} memory cards",
                "time": "2 min"
            }
        ]
        
        return {
            "ok": True,
            "total_users": total_users,
            "active_users": active_users,
            "total_cards": total_cards,
            "users_count": total_users,
            "api_status": "online",
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {
            "ok": False,
            "detail": str(e),
            "total_users": 0,
            "active_users": 0,
            "total_cards": 0
        }

# ============================================================================
# ENDPOINTS GENERALES
# ============================================================================

@app.get("/")
async def root():
    return {
        "status": "online",
        "version": "2.0.0-fixed",
        "docs": "/docs",
        "redoc": "/redoc",
        "architecture": "circular import fixed",
        "endpoints": [
            "POST /api/login",
            "GET /api/users", 
            "GET /api/memory-cards",
            "POST /api/memory-cards",
            "GET /api/memory-cards/{id}",
            "PUT /api/memory-cards/{id}",
            "DELETE /api/memory-cards/{id}",
            "GET /api/dashboard/stats",
            "GET /api/health"
        ],
        "database": "connected" if db.is_connected() else "disconnected"
    }

@app.get("/api/health")
async def health_basic():
    """Health check básico (sin auth)"""
    try:
        # Verificar conexión a la base de datos usando instancia db
        if not db.is_connected():
            return {
                "ok": False,
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Contar usuarios usando instancia db
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
            "database": "error",
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
    print("🚀 FirefighterAI FastAPI - CORREGIDO")
    print("=" * 60)
    print(f"💻 Sistema: {os_name}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    print("🌐 Servidor: http://0.0.0.0:5000")
    print("📦 Arquitectura: Sin importaciones circulares")
    print("📚 Docs: http://localhost:5000/docs")
    print("📊 Database: MongoDB Atlas via instancia db")
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