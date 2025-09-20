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
@app.get("/api/health")
def health():
    try:
        # Test DB connection
        client.server_info()
        user_count = users.count_documents({})
        return jsonify({
            "ok": True, 
            "service": "auth-api", 
            "db": DB_NAME,
            "users_count": user_count,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "ok": False, 
            "service": "auth-api", 
            "error": str(e)
        }), 500

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

        token = make_jwt({
            "sub": u["_id"], 
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
    try:
        # TODO: Aquí deberías verificar que el usuario sea admin
        # auth_header = request.headers.get('Authorization')
        # if not auth_header or not auth_header.startswith('Bearer '):
        #     return jsonify({"ok": False, "detail": "Token requerido"}), 401
        
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