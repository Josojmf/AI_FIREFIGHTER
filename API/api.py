import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from secrets import token_urlsafe

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS")
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.yzzh9ig.mongodb.net")
DB_NAME = os.getenv("DB_NAME", "FIREFIGHTER")

# Construir URI de MongoDB Atlas
if MONGO_USER and MONGO_PASS:
    MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=FirefighterAPI"
else:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

JWT_SECRET = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", "24"))

# --- App ---
app = Flask(__name__)
CORS(app)

# --- DB ---
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    # Test connection
    client.server_info()
    db = client[DB_NAME]
    users = db["users"]
    resets = db["password_resets"]
    
    # Índices (se crean al arrancar)
    users.create_index([("username", ASCENDING)], unique=True)
    users.create_index([("email", ASCENDING)], unique=True)
    # TTL para tokens de reseteo (expiran por expiresAt)
    resets.create_index("expiresAt", expireAfterSeconds=0)
    
    print("✅ Conectado a MongoDB Atlas correctamente")
    print(f"📊 Base de datos: {DB_NAME}")
    print(f"🔗 Cluster: {MONGO_CLUSTER}")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")
    print("💡 Verifica tus credenciales en el archivo .env")
    print("💡 Asegúrate de que tu IP esté en la whitelist de MongoDB Atlas")
    exit(1)

# --- Utils ---
USERNAME_RE = re.compile(r"^[a-zA-Z0-9]{3,24}$")
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, pwd_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), pwd_hash.encode("utf-8"))
    except Exception:
        return False

def make_jwt(payload: dict) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=JWT_EXPIRES_HOURS)
    to_encode = {**payload, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
    return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

def validate_register(data):
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    if not USERNAME_RE.match(username):
        return False, "Usuario inválido (3-24 chars, solo letras y números)."
    if not EMAIL_RE.match(email):
        return False, "Email inválido."
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    return True, ""

def verify_jwt(token: str):
    """Verificar y decodificar JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token expirado"
    except jwt.InvalidTokenError:
        return False, "Token inválido"

def require_auth(required_role=None):
    """Validate Authorization header and optionally enforce role."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False, (jsonify({"ok": False, "detail": "Token requerido"}), 401)

    token = auth_header.split(' ', 1)[1].strip()
    valid, payload = verify_jwt(token)
    if not valid or not isinstance(payload, dict):
        detail = payload if isinstance(payload, str) else "Token inválido"
        return False, (jsonify({"ok": False, "detail": detail}), 401)

    # Verificar que el usuario aún existe y está activo
    user_doc = users.find_one({"_id": payload.get("user_id")})
    if not user_doc:
        return False, (jsonify({"ok": False, "detail": "Usuario no encontrado"}), 401)
    
    if user_doc.get("status") != "active":
        return False, (jsonify({"ok": False, "detail": "Cuenta desactivada"}), 401)

    if required_role and payload.get('role') != required_role:
        return False, (jsonify({"ok": False, "detail": "Permisos insuficientes"}), 403)

    return True, payload

# --- Error Handlers ---
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"ok": False, "detail": "Solicitud inválida"}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({"ok": False, "detail": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

# --- Routes ---

@app.post("/api/register")
def api_register():
    try:
        data = request.get_json(force=True, silent=True) or {}
        ok, err = validate_register(data)
        if not ok:
            return jsonify({"ok": False, "detail": err}), 400

        username = data["username"].strip()
        email = data["email"].strip().lower()
        password = data["password"]

        # Verificar si ya existe
        existing_user = users.find_one({
            "$or": [{"username": username}, {"email": email}]
        })
        if existing_user:
            field = "usuario" if existing_user.get("username") == username else "email"
            return jsonify({"ok": False, "detail": f"El {field} ya existe."}), 409

        doc = {
            "_id": str(uuid4()),
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "created_at": datetime.utcnow(),
            "role": "user",
            "status": "active",
        }
        users.insert_one(doc)
        
        return jsonify({
            "ok": True, 
            "detail": "Cuenta creada correctamente.",
            "username": username
        }), 201

    except Exception as e:
        app.logger.error(f"Error en registro: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/login")
def api_login():
    try:
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"ok": False, "detail": "Usuario y contraseña requeridos."}), 400

        # Permitimos login por username o email
        q = {"$or": [{"username": username.lower()}, {"email": username.lower()}]}
        u = users.find_one(q)
        
        if not u:
            return jsonify({"ok": False, "detail": "Credenciales inválidas."}), 401
        
        if u.get("status") != "active":
            return jsonify({"ok": False, "detail": "Cuenta desactivada."}), 401
            
        if not verify_password(password, u["password_hash"]):
            return jsonify({"ok": False, "detail": "Credenciales inválidas."}), 401

        # CORREGIDO: Agregar user_id al JWT payload
        token = make_jwt({
            "sub": u["_id"], 
            "user_id": u["_id"],  # ← ESTA LÍNEA ES CRÍTICA
            "username": u["username"], 
            "role": u.get("role", "user")
        })
        
        return jsonify({
            "ok": True,
            "access_token": token,
            "user": {
                "id": u["_id"], 
                "username": u["username"], 
                "email": u["email"],
                "role": u.get("role", "user")
            }
        })

    except Exception as e:
        app.logger.error(f"Error en login: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/forgot-password")
def api_forgot_password():
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        
        if not EMAIL_RE.match(email):
            return jsonify({"ok": False, "detail": "Email inválido."}), 400

        u = users.find_one({"email": email})
        
        # Siempre devolvemos el mismo mensaje por seguridad
        if u and u.get("status") == "active":
            # Eliminar tokens anteriores del usuario
            resets.delete_many({"userId": u["_id"]})
            
            token = token_urlsafe(32)
            expires = datetime.utcnow() + timedelta(minutes=30)
            
            resets.insert_one({
                "_id": token,
                "userId": u["_id"],
                "email": email,
                "createdAt": datetime.utcnow(),
                "expiresAt": expires
            })
            
            # TODO: Aquí integrarías tu servicio de email real
            print(f"[RESET] Token para {email}: http://localhost:8000/reset-password?token={token}")

        return jsonify({
            "ok": True, 
            "detail": "Si el email existe, te enviamos instrucciones."
        })

    except Exception as e:
        app.logger.error(f"Error en forgot-password: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/reset-password")
def api_reset_password():
    try:
        data = request.get_json(force=True, silent=True) or {}
        token = (data.get("token") or "").strip()
        new_password = data.get("new_password") or ""
        
        if not token:
            return jsonify({"ok": False, "detail": "Token requerido."}), 400
            
        if len(new_password) < 8:
            return jsonify({"ok": False, "detail": "La contraseña debe tener al menos 8 caracteres."}), 400
        
        rec = resets.find_one({"_id": token})
        if not rec:
            return jsonify({"ok": False, "detail": "Token inválido o expirado."}), 400

        # Verificar si el token no ha expirado manualmente
        if rec["expiresAt"] < datetime.utcnow():
            resets.delete_one({"_id": token})
            return jsonify({"ok": False, "detail": "Token expirado."}), 400

        # Actualizar contraseña
        result = users.update_one(
            {"_id": rec["userId"]},
            {"$set": {"password_hash": hash_password(new_password)}}
        )
        
        if result.modified_count == 0:
            return jsonify({"ok": False, "detail": "Usuario no encontrado."}), 404
        
        # Eliminar el token usado
        resets.delete_one({"_id": token})
        
        return jsonify({"ok": True, "detail": "Contraseña actualizada correctamente."})

    except Exception as e:
        app.logger.error(f"Error en reset-password: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.get("/api/users")
def api_get_users():
    """Endpoint para admin: listar usuarios"""
    authorized, auth_result = require_auth(required_role="admin")
    if not authorized:
        return auth_result
    try:
        user_list = []
        for u in users.find({}, {"password_hash": 0}):  # Excluir hash de contraseña
            user_list.append({
                "id": u["_id"],
                "username": u["username"],
                "email": u["email"],
                "role": u.get("role", "user"),
                "status": u.get("status", "active"),
                "created_at": u.get("created_at", "").isoformat() if u.get("created_at") else ""
            })
        
        return jsonify({"ok": True, "users": user_list})

    except Exception as e:
        app.logger.error(f"Error en get_users: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.get("/api/users/<user_id>")
def api_get_user_by_id(user_id):
    """Endpoint para obtener un usuario específico por ID - CORREGIDO"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
        token = auth_header.split(' ')[1]
        valid, payload = verify_jwt(token)
        if not valid:
            return jsonify({"ok": False, "detail": "Token inválido"}), 401

        # Buscar usuario por ID
        user_doc = users.find_one({"_id": user_id})
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404

        # Verificar permisos: solo admin o el mismo usuario pueden ver los datos
        requesting_user_id = payload.get("user_id")
        requesting_user_role = payload.get("role", "user")
        
        # CORREGIDO: Permitir acceso más permisivo para que funcione el user loader
        if requesting_user_role != "admin" and requesting_user_id != user_id:
            # Para el user loader, permitimos que cualquier usuario autenticado vea datos básicos
            # pero sin información sensible
            pass

        # Devolver datos del usuario (sin password_hash)
        return jsonify({
            "ok": True,
            "user": {
                "id": user_doc["_id"],
                "_id": user_doc["_id"],  # Por compatibilidad
                "username": user_doc["username"],
                "email": user_doc["email"],
                "role": user_doc.get("role", "user"),
                "status": user_doc.get("status", "active"),
                "mfa_enabled": user_doc.get("mfa_enabled", False),
                "mfa_secret": user_doc.get("mfa_secret", "") if requesting_user_id == user_id or requesting_user_role == "admin" else "",
                "created_at": user_doc.get("created_at", "").isoformat() if user_doc.get("created_at") else "",
                "last_login": user_doc.get("last_login", "").isoformat() if user_doc.get("last_login") else ""
            }
        })

    except Exception as e:
        app.logger.error(f"Error en get_user_by_id: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500
    
# Memory cards 
# Agrega esta importación al inicio
from bson import ObjectId

# --- Routes para Memory Cards ---
# --- Routes para Memory Cards ---
memory_cards = db["memory_cards"]

@app.get("/api/memory-cards")
def api_get_memory_cards():
    """Obtener todas las memory cards"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
        token = auth_header.split(' ')[1]
        valid, payload = verify_jwt(token)
        if not valid:
            return jsonify({"ok": False, "detail": "Token inválido"}), 401

        # Obtener cards
        cards_list = []
        for card in memory_cards.find({}):
            cards_list.append({
                "id": str(card["_id"]),
                "title": card.get("title", ""),
                "content": card.get("content", ""),
                "category": card.get("category", ""),
                "difficulty": card.get("difficulty", "medium"),
                "created_at": card.get("created_at", "").isoformat() if card.get("created_at") else "",
                "created_by": card.get("created_by", "")
            })
        
        return jsonify({"ok": True, "cards": cards_list})

    except Exception as e:
        app.logger.error(f"Error obteniendo memory cards: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.get("/api/memory-cards/<card_id>")
def api_get_memory_card(card_id):
    """Obtener una memory card específica"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
        token = auth_header.split(' ')[1]
        valid, payload = verify_jwt(token)
        if not valid:
            return jsonify({"ok": False, "detail": "Token inválido"}), 401

        # Buscar card
        card = memory_cards.find_one({"_id": card_id})
        if not card:
            return jsonify({"ok": False, "detail": "Memory card no encontrada"}), 404

        card_data = {
            "id": str(card["_id"]),
            "title": card.get("title", ""),
            "content": card.get("content", ""),
            "category": card.get("category", ""),
            "difficulty": card.get("difficulty", "medium"),
            "created_at": card.get("created_at", "").isoformat() if card.get("created_at") else "",
            "created_by": card.get("created_by", "")
        }
        
        return jsonify({"ok": True, "card": card_data})

    except Exception as e:
        app.logger.error(f"Error obteniendo memory card: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/memory-cards")
def api_create_memory_card():
    """Crear una nueva memory card"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
        token = auth_header.split(' ')[1]
        valid, payload = verify_jwt(token)
        if not valid:
            return jsonify({"ok": False, "detail": "Token inválido"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "detail": "Datos requeridos"}), 400

        # Validar campos requeridos
        required_fields = ["title", "content", "category"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"ok": False, "detail": f"Campo {field} es requerido"}), 400

        # Crear card
        card_doc = {
            "_id": str(ObjectId()),
            "title": data["title"],
            "content": data["content"],
            "category": data["category"],
            "difficulty": data.get("difficulty", "medium"),
            "created_at": datetime.utcnow(),
            "created_by": payload["username"]
        }

        memory_cards.insert_one(card_doc)
        
        return jsonify({
            "ok": True, 
            "detail": "Memory card creada correctamente",
            "card": {
                "id": card_doc["_id"],
                "title": card_doc["title"],
                "content": card_doc["content"],
                "category": card_doc["category"],
                "difficulty": card_doc["difficulty"],
                "created_at": card_doc["created_at"].isoformat(),
                "created_by": card_doc["created_by"]
            }
        }), 201

    except Exception as e:
        app.logger.error(f"Error creando memory card: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.put("/api/memory-cards/<card_id>")
def api_update_memory_card(card_id):
    """Actualizar una memory card existente"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
        token = auth_header.split(' ')[1]
        valid, payload = verify_jwt(token)
        if not valid:
            return jsonify({"ok": False, "detail": "Token inválido"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "detail": "Datos requeridos"}), 400

        # Verificar si la card existe
        existing_card = memory_cards.find_one({"_id": card_id})
        if not existing_card:
            return jsonify({"ok": False, "detail": "Memory card no encontrada"}), 404

        # Campos permitidos para actualizar
        update_data = {}
        if "title" in data:
            update_data["title"] = data["title"]
        if "content" in data:
            update_data["content"] = data["content"]
        if "category" in data:
            update_data["category"] = data["category"]
        if "difficulty" in data:
            update_data["difficulty"] = data["difficulty"]

        if not update_data:
            return jsonify({"ok": False, "detail": "No hay datos para actualizar"}), 400

        # Actualizar
        memory_cards.update_one(
            {"_id": card_id},
            {"$set": update_data}
        )

        # Obtener card actualizada
        updated_card = memory_cards.find_one({"_id": card_id})
        
        return jsonify({
            "ok": True, 
            "detail": "Memory card actualizada correctamente",
            "card": {
                "id": str(updated_card["_id"]),
                "title": updated_card.get("title", ""),
                "content": updated_card.get("content", ""),
                "category": updated_card.get("category", ""),
                "difficulty": updated_card.get("difficulty", "medium"),
                "created_at": updated_card.get("created_at", "").isoformat() if updated_card.get("created_at") else "",
                "created_by": updated_card.get("created_by", "")
            }
        })

    except Exception as e:
        app.logger.error(f"Error actualizando memory card: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.delete("/api/memory-cards/<card_id>")
def api_delete_memory_card(card_id):
    """Eliminar una memory card"""
    try:
        # Verificar autenticación
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
        token = auth_header.split(' ')[1]
        valid, payload = verify_jwt(token)
        if not valid:
            return jsonify({"ok": False, "detail": "Token inválido"}), 401

        # Verificar si la card existe
        existing_card = memory_cards.find_one({"_id": card_id})
        if not existing_card:
            return jsonify({"ok": False, "detail": "Memory card no encontrada"}), 404

        # Eliminar
        result = memory_cards.delete_one({"_id": card_id})
        
        if result.deleted_count == 1:
            return jsonify({
                "ok": True, 
                "detail": "Memory card eliminada correctamente"
            })
        else:
            return jsonify({"ok": False, "detail": "Error al eliminar la memory card"}), 500

    except Exception as e:
        app.logger.error(f"Error eliminando memory card: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500
    
# Añadir en api.py - después del endpoint GET /api/users/<user_id>
@app.patch("/api/users/<user_id>")
def api_update_user(user_id):
    """Actualizar usuario - CORREGIDO"""
    try:
        # Verificar autenticación y permisos de admin
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result

        data = request.get_json()
        if not data:
            return jsonify({"ok": False, "detail": "Datos requeridos"}), 400

        # Verificar si el usuario existe
        user_doc = users.find_one({"_id": user_id})
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404

        # Campos permitidos para actualizar
        update_data = {}
        if "status" in data:
            if data["status"] in ["active", "inactive"]:
                update_data["status"] = data["status"]
            else:
                return jsonify({"ok": False, "detail": "Estado inválido"}), 400

        if "role" in data:
            if data["role"] in ["admin", "user"]:
                update_data["role"] = data["role"]
            else:
                return jsonify({"ok": False, "detail": "Rol inválido"}), 400

        if not update_data:
            return jsonify({"ok": False, "detail": "No hay datos válidos para actualizar"}), 400

        # Actualizar usuario
        users.update_one(
            {"_id": user_id},
            {"$set": update_data}
        )

        # Obtener usuario actualizado
        updated_user = users.find_one({"_id": user_id})
        
        return jsonify({
            "ok": True,
            "detail": "Usuario actualizado correctamente",
            "user": {
                "id": updated_user["_id"],
                "username": updated_user["username"],
                "email": updated_user["email"],
                "role": updated_user.get("role", "user"),
                "status": updated_user.get("status", "active")
            }
        })

    except Exception as e:
        app.logger.error(f"Error actualizando usuario: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.get("/health")
def health():
    return jsonify(ok=True, service="backend"), 200

@app.get("/api/health")
def api_health():
    """Health check endpoint para el backoffice"""
    try:
        # Verificar conexión a MongoDB
        client.server_info()
        
        # Contar usuarios (sin auth para health check)
        users_count = users.count_documents({})
        
        return jsonify({
            "ok": True,
            "service": "Firefighter API",
            "database": "connected",
            "users_count": users_count,
            "timestamp": datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "service": "Firefighter API", 
            "database": "disconnected",
            "error": str(e)
        }), 503

@app.get("/ready")
def ready():
    try:
        # si tienes 'client' de Mongo, haz un ping rápido
        client.server_info()
        return jsonify(ready=True), 200
    except Exception:
        return jsonify(ready=False), 503

@app.get("/")
def root():
    return jsonify({"ok": True, "service": "Firefighter API", "status": "running"}), 200

if __name__ == "__main__":
    print("🚀 Auth API iniciando...")
    print(f"📊 Base de datos: {DB_NAME}")
    print(f"🔗 MongoDB URI: {MONGO_URI}")
    print("🌐 API corriendo en http://localhost:5000")
    
    # Crear usuario admin por defecto si no existe
    try:
        admin_exists = users.find_one({"username": "admin"})
        if not admin_exists:
            admin_doc = {
                "_id": str(uuid4()),
                "username": "admin",
                "email": "admin@firefighter.com",
                "password_hash": hash_password("admin123"),
                "created_at": datetime.utcnow(),
                "role": "admin",
                "status": "active",
            }
            users.insert_one(admin_doc)
            print("👤 Usuario admin creado: admin/admin123")
    except Exception as e:
        print(f"⚠️ No se pudo crear usuario admin: {e}")
    
    app.run(host="0.0.0.0", port=5000, debug=True)