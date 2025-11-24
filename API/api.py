import os
import re
import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from secrets import token_urlsafe
import docker
import subprocess
import json
from threading import Thread
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import load_dotenv

import pyotp
import qrcode
import io
import base64

from bson import ObjectId

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

# --- MFA Functions ---
def generate_mfa_secret():
    """Generar secreto MFA"""
    return pyotp.random_base32()

def generate_qr_code(username, secret):
    """Generar código QR para MFA"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="FirefighterAI"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_base64}"

def verify_mfa_token(secret, token):
    """Verificar token MFA"""
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    except Exception:
        return False

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
        role = data.get("role", "user")

        # Verificar si ya existe
        existing_user = users.find_one({
            "$or": [{"username": username}, {"email": email}]
        })
        if existing_user:
            field = "usuario" if existing_user.get("username") == username else "email"
            return jsonify({"ok": False, "detail": f"El {field} ya existe."}), 409

        # 🔥 ESTRUCTURA EMBEBIDA: Usuario con leitner_progress
        doc = {
            "_id": str(uuid4()),
            "username": username,
            "email": email,
            "password_hash": hash_password(password),
            "created_at": datetime.now(timezone.utc),
            "role": role,
            "status": "active",
            "mfa_enabled": False,
            "mfa_secret": "",
            # 🎯 LEITNER PROGRESS PARA TODOS LOS USUARIOS
            "leitner_progress": {
                "cards": [],
                "stats": {
                    "total_cards": 0, "cards_by_box": {}, "last_study_session": None,
                    "total_reviews": 0, "correct_answers": 0, "accuracy_rate": 0.0,
                    "study_streak": 0, "cards_mastered": 0
                },
                "settings": {
                    "daily_goal": 20, "preferred_decks": [], "notification_enabled": True,
                    "study_reminders": "18:00", "auto_advance": True
                },
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }
        
        # 👑 BACKOFFICE CARDS SOLO PARA ADMINS
        if role == "admin":
            doc["backoffice_cards"] = {
                "cards": [], "total_cards": 0, "categories": [],
                "created_at": datetime.now(timezone.utc),
                "auto_populated": False
            }
            
            # Intentar auto-poblar desde memory_cards
            try:
                if "memory_cards" in db.list_collection_names():
                    memory_cards = list(db["memory_cards"].find({}))
                    if memory_cards:
                        backoffice_cards = [{
                            "id": str(card["_id"]), "title": card.get("title", ""),
                            "content": card.get("content", ""), "category": card.get("category", "general"),
                            "difficulty": card.get("difficulty", "medium"), "created_at": card.get("created_at"),
                            "created_by": card.get("created_by", "admin"), "migrated_from": "memory_cards"
                        } for card in memory_cards]
                        doc["backoffice_cards"].update({
                            "cards": backoffice_cards, "total_cards": len(backoffice_cards),
                            "categories": list(set(c["category"] for c in backoffice_cards)),
                            "auto_populated": True
                        })
            except Exception:
                pass  # Ignorar errores de auto-población

        users.insert_one(doc)
        
        # Log y respuesta
        components = ["leitner_progress"]
        if role == "admin":
            components.append(f"backoffice_cards ({doc['backoffice_cards']['total_cards']} cards)")
            
        app.logger.info(f"Usuario '{username}' creado con estructura embebida: {components}")
        
        return jsonify({
            "ok": True, 
            "detail": "Cuenta creada con estructura embebida.",
            "username": username,
            "embedded_structure": True,
            "components": components
        }), 201

    except Exception as e:
        app.logger.error(f"Error en registro embebido: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/login")
def api_login():
    try:
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({"ok": False, "detail": "Usuario y contraseña requeridos."}), 400

        # Buscar usuario por username o email
        q = {"$or": [{"username": username.lower()}, {"email": username.lower()}]}
        user_doc = users.find_one(q)

        if not user_doc or not verify_password(password, user_doc["password_hash"]):
            return jsonify({"ok": False, "detail": "Credenciales incorrectas."}), 401

        if user_doc.get("status") != "active":
            return jsonify({"ok": False, "detail": "Cuenta desactivada."}), 401

        # Verificar MFA si está habilitado
        if user_doc.get("mfa_enabled", False):
            mfa_token = data.get("mfa_token", "").strip()
            if not mfa_token:
                return jsonify({
                    "ok": False, 
                    "detail": "Token MFA requerido",
                    "mfa_required": True
                }), 401
            
            # Verificar token MFA
            secret = user_doc.get("mfa_secret", "")
            if not secret or not verify_mfa_token(secret, mfa_token):
                return jsonify({"ok": False, "detail": "Token MFA inválido"}), 401

        # Crear JWT
        token = make_jwt({
            "user_id": user_doc["_id"],
            "username": user_doc["username"],
            "role": user_doc.get("role", "user")
        })

        return jsonify({
            "ok": True,
            "access_token": token,
            "user": {
                "username": user_doc["username"], 
                "email": user_doc["email"],
                "role": user_doc.get("role", "user"),
                "mfa_enabled": user_doc.get("mfa_enabled", False)
            }
        }), 200

    except Exception as e:
        app.logger.error(f"Error en login: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/forgot-password")
def api_forgot_password():
    try:
        data = request.get_json(force=True, silent=True) or {}
        email = (data.get("email") or "").strip().lower()

        if not email:
            return jsonify({"ok": False, "detail": "Email requerido"}), 400

        user_doc = users.find_one({"email": email})
        if not user_doc:
            # Por seguridad, no revelar si el email existe
            return jsonify({"ok": True, "detail": "Si el email existe, recibirás un enlace de recuperación"}), 200

        # Crear token de reseteo
        reset_token = token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        resets.insert_one({
            "userId": user_doc["_id"],
            "token": reset_token,
            "expiresAt": expires_at,
            "used": False
        })

        # En un entorno real, enviarías un email aquí
        print(f"🔗 Reset token para {email}: {reset_token}")

        return jsonify({"ok": True, "detail": "Si el email existe, recibirás un enlace de recuperación"}), 200

    except Exception as e:
        app.logger.error(f"Error en forgot-password: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/reset-password")
def api_reset_password():
    try:
        data = request.get_json(force=True, silent=True) or {}
        token = (data.get("token") or "").strip()
        new_password = data.get("password") or ""

        if not token or not new_password:
            return jsonify({"ok": False, "detail": "Token y nueva contraseña requeridos"}), 400

        if len(new_password) < 8:
            return jsonify({"ok": False, "detail": "La contraseña debe tener al menos 8 caracteres"}), 400

        # Buscar token válido
        reset_doc = resets.find_one({
            "token": token,
            "used": False,
            "expiresAt": {"$gt": datetime.utcnow()}
        })

        if not reset_doc:
            return jsonify({"ok": False, "detail": "Token inválido o expirado"}), 400

        # Actualizar contraseña
        new_hash = hash_password(new_password)
        users.update_one(
            {"_id": reset_doc["userId"]},
            {"$set": {"password_hash": new_hash}}
        )

        # Marcar token como usado
        resets.update_one(
            {"_id": reset_doc["_id"]},
            {"$set": {"used": True}}
        )

        return jsonify({"ok": True, "detail": "Contraseña actualizada correctamente"}), 200

    except Exception as e:
        app.logger.error(f"Error en reset-password: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

# --- Memory Cards Routes ---
memory_cards = db["leitner_cards"]

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
                "title": card.get("title") or card.get("front", ""),
                "content": card.get("content") or card.get("back", ""),
                "category": card.get("category") or card.get("deck", ""),
                "difficulty": card.get("difficulty", "medium"),
                "created_at": card.get("created_at", "").isoformat() if card.get("created_at") else "",
                "created_by": card.get("created_by") or card.get("user", "")
            })
        
        return jsonify({"ok": True, "cards": cards_list})

    except Exception as e:
        app.logger.error(f"Error obteniendo memory cards: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500
    
    
@app.get("/api/memory-cards/<card_id>")
def api_get_memory_card(card_id):
    """Obtener una memory card específica por ID - CORREGIDO"""
    try:
        # Verificar autenticación - solo admin
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result
        
        # 🔧 CORRIGIDO: Buscar por string ID y ObjectId
        card = None
        
        # Intentar primero como string (nuevo formato)
        card = memory_cards.find_one({"_id": card_id})
        
        # Si no encuentra, intentar como ObjectId (formato MongoDB)
        if not card:
            try:
                card = memory_cards.find_one({"_id": ObjectId(card_id)})
                print(f"🔍 Memory card encontrada con ObjectId: {card_id}")
            except:
                print(f"❌ ID no válido como ObjectId: {card_id}")
        
        if not card:
            app.logger.warning(f"Memory card {card_id} no encontrada en ningún formato")
            return jsonify({"ok": False, "detail": "Memory card no encontrada"}), 404
        
        # Formatear respuesta - manejar tanto ObjectId como string
        card_id_str = str(card["_id"])
        
        card_data = {
            "id": card_id_str,
            "_id": card_id_str,  # Por compatibilidad
            "title": card.get("title") or card.get("front", ""),
            "content": card.get("content") or card.get("back", ""),
            "category": card.get("category") or card.get("deck", "general"),
            "difficulty": card.get("difficulty", "medium"),
            "created_at": card.get("created_at", "").isoformat() if card.get("created_at") else "",
            "created_by": card.get("created_by") or card.get("user", "system"),
            "tags": card.get("tags", []),
            "source": card.get("source", ""),
            "updated_at": card.get("updated_at", "").isoformat() if card.get("updated_at") else ""
        }
        
        print(f"✅ Memory card {card_id} encontrada y formateada")
        return jsonify({"ok": True, "card": card_data})
        
    except Exception as e:
        app.logger.error(f"Error obteniendo memory card {card_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.put("/api/memory-cards/<card_id>")
def api_update_memory_card(card_id):
    """Actualizar una memory card específica - CORREGIDO"""
    try:
        # Verificar autenticación - solo admin
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result
        
        data = request.json
        if not data:
            return jsonify({"ok": False, "detail": "Datos requeridos"}), 400
        
        # 🔧 CORRIGIDO: Determinar formato de ID a usar
        search_id = card_id
        try:
            # Si es válido como ObjectId, usarlo
            if len(card_id) == 24:
                search_id = ObjectId(card_id)
        except:
            # Si no, usar como string
            search_id = card_id
        
        # Preparar datos de actualización
        update_data = {
            "updated_at": datetime.now(timezone.utc)
        }
        
        # Campos permitidos para actualizar
        allowed_fields = ["title", "content", "category", "difficulty", "tags", "source", "front", "back", "deck"]
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        # Actualizar en MongoDB
        result = memory_cards.update_one(
            {"_id": search_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({"ok": False, "detail": "Memory card no encontrada"}), 404
        
        if result.modified_count == 0:
            return jsonify({"ok": True, "detail": "No hay cambios que aplicar"})
        
        # Obtener card actualizada
        updated_card = memory_cards.find_one({"_id": search_id})
        card_data = {
            "id": str(updated_card["_id"]),
            "title": updated_card.get("title") or updated_card.get("front", ""),
            "content": updated_card.get("content") or updated_card.get("back", ""),
            "category": updated_card.get("category") or updated_card.get("deck", "general"),
            "difficulty": updated_card.get("difficulty", "medium"),
            "updated_at": updated_card.get("updated_at", "").isoformat() if updated_card.get("updated_at") else ""
        }
        
        return jsonify({"ok": True, "detail": "Memory card actualizada", "card": card_data})
        
    except Exception as e:
        app.logger.error(f"Error actualizando memory card {card_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.delete("/api/memory-cards/<card_id>")
def api_delete_memory_card(card_id):
    """Eliminar una memory card específica - CORREGIDO"""
    try:
        # Verificar autenticación - solo admin
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result
        
        # 🔧 CORRIGIDO: Determinar formato de ID a usar
        search_id = card_id
        try:
            # Si es válido como ObjectId, usarlo
            if len(card_id) == 24:
                search_id = ObjectId(card_id)
        except:
            # Si no, usar como string
            search_id = card_id
        
        # Eliminar de MongoDB
        result = memory_cards.delete_one({"_id": search_id})
        
        if result.deleted_count == 0:
            return jsonify({"ok": False, "detail": "Memory card no encontrada"}), 404
        
        return jsonify({"ok": True, "detail": "Memory card eliminada correctamente"})
        
    except Exception as e:
        app.logger.error(f"Error eliminando memory card {card_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

# --- Users Management ---
@app.get("/api/users")
def api_get_users():
    """Obtener lista de usuarios - Solo admin"""
    try:
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result

        users_list = []
        for user in users.find({}):
            users_list.append({
                "id": user["_id"],
                "username": user["username"],
                "email": user["email"],
                "role": user.get("role", "user"),
                "status": user.get("status", "active"),
                "created_at": user.get("created_at", "").isoformat() if user.get("created_at") else "",
                "mfa_enabled": user.get("mfa_enabled", False),
                "has_leitner_progress": "leitner_progress" in user,
                "has_backoffice_cards": "backoffice_cards" in user
            })
        
        return jsonify({"ok": True, "users": users_list})

    except Exception as e:
        app.logger.error(f"Error obteniendo usuarios: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500
    

@app.get("/api/users/<user_id>")
def api_get_user(user_id):
    """Obtener un usuario específico por ID - Solo admin"""
    try:
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result

        user_doc = users.find_one({"_id": user_id})
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404

        return jsonify({
            "ok": True,
            "user": {
                "id": user_doc["_id"],
                "username": user_doc["username"],
                "email": user_doc["email"],
                "role": user_doc.get("role", "user"),
                "status": user_doc.get("status", "active"),
                "created_at": user_doc.get("created_at", "").isoformat() if user_doc.get("created_at") else "",
                "mfa_enabled": user_doc.get("mfa_enabled", False),
                "has_leitner_progress": "leitner_progress" in user_doc,
                "has_backoffice_cards": "backoffice_cards" in user_doc
            }
        })

    except Exception as e:
        app.logger.error(f"Error obteniendo usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.get("/api/users/<user_id>/progress")
def api_get_user_progress(user_id):
    """Obtener progreso detallado de un usuario con memory cards"""
    try:
        # Verificar autenticación - solo admin
        authorized, auth_result = require_auth(required_role="admin")
        if not authorized:
            return auth_result
        
        # Buscar usuario por ID (manejar ObjectId y string)
        user_doc = None
        try:
            user_doc = users.find_one({"_id": user_id})
        except:
            pass
        
        if not user_doc:
            try:
                user_doc = users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404
        
        # Obtener progreso Leitner
        leitner_progress = user_doc.get("leitner_progress", {})
        leitner_stats = leitner_progress.get("stats", {})
        leitner_cards = leitner_progress.get("cards", [])
        
        # Calcular estadísticas de cards
        total_cards = leitner_stats.get("total_cards", 0)
        total_reviews = leitner_stats.get("total_reviews", 0)
        correct_answers = leitner_stats.get("correct_answers", 0)
        accuracy_rate = leitner_stats.get("accuracy_rate", 0.0)
        cards_mastered = leitner_stats.get("cards_mastered", 0)
        study_streak = leitner_stats.get("study_streak", 0)
        
        # Calcular distribución por boxes (Leitner)
        cards_by_box = leitner_stats.get("cards_by_box", {})
        box_distribution = {
            "box_1": cards_by_box.get("1", 0),
            "box_2": cards_by_box.get("2", 0),
            "box_3": cards_by_box.get("3", 0),
            "box_4": cards_by_box.get("4", 0),
            "box_5": cards_by_box.get("5", 0),
        }
        
        # Progreso por categorías
        category_progress = {}
        for card in leitner_cards:
            category = card.get("category", "general")
            if category not in category_progress:
                category_progress[category] = {
                    "total": 0,
                    "correct": 0,
                    "incorrect": 0,
                    "accuracy": 0.0
                }
            
            category_progress[category]["total"] += 1
            if card.get("correct", False):
                category_progress[category]["correct"] += 1
            else:
                category_progress[category]["incorrect"] += 1
        
        # Calcular accuracy por categoría
        for category in category_progress:
            total = category_progress[category]["total"]
            correct = category_progress[category]["correct"]
            if total > 0:
                category_progress[category]["accuracy"] = round((correct / total) * 100, 1)
        
        # Actividad reciente (últimas 7 sessions simuladas)
        last_study = leitner_stats.get("last_study_session")
        recent_activity = []
        
        if last_study:
            import random
            from datetime import timedelta
            
            # Simular actividad de los últimos 7 días
            for i in range(7):
                date = datetime.now(timezone.utc) - timedelta(days=i)
                cards_studied = random.randint(0, 25) if random.random() > 0.2 else 0
                recent_activity.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "cards_studied": cards_studied,
                    "accuracy": round(random.uniform(0.6, 0.95) * 100, 1) if cards_studied > 0 else 0
                })
        
        # Obtener backoffice cards del usuario
        backoffice_cards = user_doc.get("backoffice_cards", {})
        total_backoffice_cards = backoffice_cards.get("total_cards", 0)
        
        progress_data = {
            "user_id": str(user_doc["_id"]),
            "username": user_doc["username"],
            "email": user_doc["email"],
            
            # Estadísticas generales
            "general_stats": {
                "total_cards": total_cards,
                "total_reviews": total_reviews,
                "correct_answers": correct_answers,
                "incorrect_answers": total_reviews - correct_answers,
                "accuracy_rate": round(accuracy_rate * 100, 1),
                "cards_mastered": cards_mastered,
                "study_streak": study_streak,
                "backoffice_cards": total_backoffice_cards
            },
            
            # Distribución por boxes Leitner
            "box_distribution": box_distribution,
            
            # Progreso por categorías
            "category_progress": category_progress,
            
            # Actividad reciente
            "recent_activity": recent_activity,
            
            # Configuración de estudio
            "study_settings": leitner_progress.get("settings", {}),
            
            # Fechas importantes
            "dates": {
                "last_study": last_study.isoformat() if last_study else None,
                "account_created": user_doc.get("created_at", "").isoformat() if user_doc.get("created_at") else None,
                "progress_updated": leitner_progress.get("updated_at", "").isoformat() if leitner_progress.get("updated_at") else None
            }
        }
        
        return jsonify({"ok": True, "progress": progress_data})
        
    except Exception as e:
        app.logger.error(f"Error obteniendo progreso de usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

# --- MFA Endpoints ---
@app.post("/api/users/<user_id>/mfa/generate")
def api_generate_mfa_qr(user_id):
    """Generar QR code para MFA de un usuario - CORREGIDO"""
    try:
        # Verificar autenticación
        authorized, auth_result = require_auth()
        if not authorized:
            return auth_result
        
        # Buscar usuario por ID (manejar ObjectId y string)
        user_doc = None
        try:
            user_doc = users.find_one({"_id": user_id})
        except:
            pass
        
        if not user_doc:
            try:
                user_doc = users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404
        
        # Generar nuevo secreto MFA (siempre generar nuevo para setup)
        mfa_secret = generate_mfa_secret()
        
        # Generar QR code
        qr_code_data = generate_qr_code(user_doc["username"], mfa_secret)
        
        # Actualizar usuario con el nuevo secreto (pero no habilitar aún)
        users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {
                "mfa_secret": mfa_secret,
                "mfa_enabled": False,  # No habilitar hasta verificación
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        # Generar códigos de respaldo
        backup_codes = [f"BACKUP-{i+1:02d}-{token_urlsafe(4).upper()}" for i in range(5)]
        
        return jsonify({
            "ok": True,
            "qr_code": qr_code_data,
            "secret": mfa_secret,
            "backup_codes": backup_codes,
            "detail": "Escanea el QR con tu app de autenticación"
        })
        
    except Exception as e:
        app.logger.error(f"Error generando MFA QR para usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/users/<user_id>/mfa/verify-setup")
def api_verify_mfa_setup(user_id):
    """Verificar configuración MFA con token - ENDPOINT FALTANTE"""
    try:
        # Verificar autenticación
        authorized, auth_result = require_auth()
        if not authorized:
            return auth_result
        
        data = request.json
        if not data or 'token' not in data:
            return jsonify({"ok": False, "detail": "Token MFA requerido"}), 400
        
        # Buscar usuario por ID (manejar ObjectId y string)
        user_doc = None
        try:
            user_doc = users.find_one({"_id": user_id})
        except:
            pass
        
        if not user_doc:
            try:
                user_doc = users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404
        
        # Verificar que tiene secreto MFA configurado
        mfa_secret = user_doc.get("mfa_secret")
        if not mfa_secret:
            return jsonify({"ok": False, "detail": "MFA no configurado. Genera un QR primero."}), 400
        
        # Verificar token MFA
        if not verify_mfa_token(mfa_secret, data['token']):
            return jsonify({"ok": False, "detail": "Token MFA inválido"}), 400
        
        # Si la verificación es exitosa, habilitar MFA
        users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {
                "mfa_enabled": True,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return jsonify({
            "ok": True,
            "detail": "MFA configurado y habilitado correctamente"
        })
        
    except Exception as e:
        app.logger.error(f"Error verificando setup MFA para usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/users/<user_id>/mfa/enable")
def api_enable_user_mfa(user_id):
    """Habilitar MFA para un usuario - CORREGIDO"""
    try:
        # Verificar autenticación
        authorized, auth_result = require_auth()
        if not authorized:
            return auth_result
        
        data = request.json
        if not data or 'token' not in data:
            return jsonify({"ok": False, "detail": "Token MFA requerido"}), 400
        
        # Buscar usuario
        user_doc = None
        try:
            user_doc = users.find_one({"_id": user_id})
        except:
            pass
        
        if not user_doc:
            try:
                user_doc = users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404
        
        # Verificar que tiene secreto MFA
        mfa_secret = user_doc.get("mfa_secret")
        if not mfa_secret:
            return jsonify({"ok": False, "detail": "Primero debes generar un código QR"}), 400
        
        # Verificar token MFA
        if not verify_mfa_token(mfa_secret, data['token']):
            return jsonify({"ok": False, "detail": "Token MFA inválido"}), 400
        
        # Habilitar MFA
        users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {
                "mfa_enabled": True,
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return jsonify({
            "ok": True,
            "detail": "MFA habilitado correctamente"
        })
        
    except Exception as e:
        app.logger.error(f"Error habilitando MFA para usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/users/<user_id>/mfa/disable")
def api_disable_user_mfa(user_id):
    """Deshabilitar MFA para un usuario - CORREGIDO"""
    try:
        # Verificar autenticación - solo admin o el propio usuario
        authorized, auth_result = require_auth()
        if not authorized:
            return auth_result
        
        # Buscar usuario
        user_doc = None
        try:
            user_doc = users.find_one({"_id": user_id})
        except:
            pass
        
        if not user_doc:
            try:
                user_doc = users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404
        
        # Verificar que el usuario autenticado es el dueño o es admin
        auth_payload = auth_result
        if auth_payload.get("user_id") != user_id and auth_payload.get("role") != "admin":
            return jsonify({"ok": False, "detail": "No tienes permisos para esta acción"}), 403
        
        # Deshabilitar MFA y limpiar secreto
        users.update_one(
            {"_id": user_doc["_id"]},
            {"$set": {
                "mfa_enabled": False,
                "mfa_secret": "",
                "updated_at": datetime.now(timezone.utc)
            }}
        )
        
        return jsonify({
            "ok": True,
            "detail": "MFA deshabilitado correctamente"
        })
        
    except Exception as e:
        app.logger.error(f"Error deshabilitando MFA para usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

@app.post("/api/users/<user_id>/mfa/verify")
def api_verify_user_mfa(user_id):
    """Verificar token MFA de un usuario - CORREGIDO"""
    try:
        data = request.json
        if not data or 'token' not in data:
            return jsonify({"ok": False, "detail": "Token MFA requerido"}), 400
        
        # Buscar usuario
        user_doc = None
        try:
            user_doc = users.find_one({"_id": user_id})
        except:
            pass
        
        if not user_doc:
            try:
                user_doc = users.find_one({"_id": ObjectId(user_id)})
            except:
                pass
        
        if not user_doc:
            return jsonify({"ok": False, "detail": "Usuario no encontrado"}), 404
        
        # Verificar MFA
        mfa_secret = user_doc.get("mfa_secret")
        if not mfa_secret or not user_doc.get("mfa_enabled"):
            return jsonify({"ok": False, "detail": "MFA no habilitado"}), 400
        
        if verify_mfa_token(mfa_secret, data['token']):
            return jsonify({
                "ok": True,
                "detail": "Token MFA válido"
            })
        else:
            return jsonify({
                "ok": False,
                "detail": "Token MFA inválido"
            }), 400
        
    except Exception as e:
        app.logger.error(f"Error verificando MFA para usuario {user_id}: {e}")
        return jsonify({"ok": False, "detail": "Error interno del servidor"}), 500

# --- Health Check ---
@app.get("/health")
@app.get("/api/health")
def health_check():
    try:
        # Ping MongoDB
        client.server_info()
        
        return jsonify({
            "ok": True,
            "service": "Firefighter API",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "ok": False,
            "service": "Firefighter API", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503
        
# --- Docker Endpoints ---
@app.get("/api/docker/containers")
def api_get_docker_containers():
    """Obtener información de contenedores Docker"""
    try:
        # Verificar autenticación
        authorized, auth_result = require_auth()
        if not authorized:
            return auth_result
        
        # Simular datos de contenedores (ya que Docker no está disponible)
        simulated_containers = [
            {
                "id": "a1b2c3d4e5f6",
                "name": "firefighter-api",
                "status": "running",
                "image": "firefighter/api:latest",
                "created": "2024-01-01T12:00:00Z",
                "state": "running",
                "ports": "5000:5000"
            },
            {
                "id": "b2c3d4e5f6g7",
                "name": "firefighter-backoffice",
                "status": "running", 
                "image": "firefighter/backoffice:latest",
                "created": "2024-01-01T12:00:00Z",
                "state": "running",
                "ports": "8080:8080"
            },
            {
                "id": "c3d4e5f6g7h8",
                "name": "mongodb",
                "status": "running",
                "image": "mongo:6.0",
                "created": "2024-01-01T12:00:00Z", 
                "state": "running",
                "ports": "27017:27017"
            }
        ]
        
        return jsonify({
            "ok": True,
            "containers": simulated_containers,
            "total": len(simulated_containers),
            "simulated": True
        })
            
    except Exception as e:
        app.logger.error(f"Error obteniendo contenedores Docker: {e}")
        return jsonify({
            "ok": False, 
            "detail": "Error interno del servidor",
            "containers": [],
            "total": 0
        }), 500

@app.get("/api/docker/logs")
def api_docker_logs():
    """Endpoint para logs de Docker"""
    try:
        print("🐳 Solicitando logs de Docker...")
        
        # Simular logs de Docker (puedes reemplazar con logs reales)
        fake_logs = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "container": "api",
                "level": "INFO",
                "message": "API FirefighterAI iniciada correctamente"
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
                "container": "database",
                "level": "SUCCESS",
                "message": "Conexión MongoDB establecida"
            },
            {
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=2)).isoformat(),
                "container": "backoffice",
                "level": "INFO", 
                "message": "BackOffice iniciado en puerto 8080"
            }
        ]
        
        return jsonify({
            "ok": True,
            "logs": fake_logs,
            "count": len(fake_logs)
        })
        
    except Exception as e:
        print(f"❌ Error obteniendo logs: {e}")
        return jsonify({
            "ok": False,
            "detail": str(e),
            "logs": []
        }), 500

def get_system_logs_simulation(lines=20):
    """Generar logs simulados del sistema"""
    import random
    from datetime import datetime, timedelta
    
    levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR", "SUCCESS"]
    containers = ["api", "backoffice", "database", "nginx", "redis", "auth-service"]
    actions = [
        "Container started successfully",
        "Health check passed",
        "New user registered", 
        "Database connection established",
        "Memory usage at {}%",
        "API endpoint called: {}",
        "Backup completed successfully",
        "Security scan completed",
        "Configuration reloaded",
        "Cache cleared",
        "User authentication successful",
        "Data export completed",
        "System update available",
        "Performance optimization applied"
    ]
    
    endpoints = ["/api/users", "/api/login", "/api/dashboard", "/api/health", "/api/memory-cards"]
    
    logs = []
    base_time = datetime.now(timezone.utc)
    
    for i in range(lines):
        log_time = base_time - timedelta(seconds=random.randint(0, 300))
        level = random.choice(levels)
        container = random.choice(containers)
        
        # Seleccionar y formatear mensaje
        action_template = random.choice(actions)
        if "{}" in action_template:
            if "endpoint" in action_template:
                message = action_template.format(random.choice(endpoints))
            elif "usage" in action_template:
                message = action_template.format(random.randint(20, 85))
            else:
                message = action_template.format(random.randint(1, 100))
        else:
            message = action_template
        
        # Añadir detalles específicos por nivel
        if level == "ERROR":
            errors = ["Connection timeout", "Database unreachable", "Permission denied", "Resource not found"]
            message = f"{message} - {random.choice(errors)}"
        elif level == "WARNING":
            warnings = ["High memory usage", "Slow response time", "Retry attempt", "Deprecated API call"]
            message = f"{message} - {random.choice(warnings)}"
        elif level == "SUCCESS":
            successes = ["Operation completed", "User created", "Data saved", "Cache updated"]
            message = f"{message} - {random.choice(successes)}"
        
        logs.append({
            "timestamp": log_time.isoformat(),
            "container": container,
            "level": level,
            "message": message
        })
    
    # Ordenar por timestamp (más reciente primero)
    logs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return logs[:lines]

# Endpoint para logs en tiempo real (simulado)
@app.get("/api/docker/logs/stream")
def docker_logs_stream():
    """Endpoint simulado para logs en tiempo real"""
    try:
        authorized, auth_result = require_auth()
        if not authorized:
            return auth_result
        
        # Generar algunos logs nuevos
        new_logs = get_system_logs_simulation(5)
        
        return jsonify({
            "ok": True,
            "logs": new_logs,
            "type": "update"
        })
        
    except Exception as e:
        return jsonify({
            "ok": False,
            "detail": str(e)
        }), 500
        
        

@app.get("/api/dashboard/stats")
def api_dashboard_stats():
    """Endpoint para estadísticas del dashboard"""
    try:
        print("🔍 Solicitando estadísticas del dashboard...")
        
        # Contar usuarios totales
        total_users = users.count_documents({})
        print(f"👥 Total usuarios: {total_users}")
        
        # Contar usuarios activos (últimos 30 días)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        active_users = users.count_documents({
            "created_at": {"$gte": thirty_days_ago}
        })
        print(f"✅ Usuarios activos: {active_users}")
        
        # Contar memory cards totales
        pipeline = [
            {"$project": {"total_cards": {"$size": {"$ifNull": ["$leitner_progress.cards", []]}}}},
            {"$group": {"_id": None, "total": {"$sum": "$total_cards"}}}
        ]
        cards_result = list(users.aggregate(pipeline))
        total_cards = cards_result[0]["total"] if cards_result else 0
        print(f"🗃️ Total memory cards: {total_cards}")
        
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
            },
            {
                "icon": "🔄",
                "text": "Sistema funcionando correctamente",
                "time": "3 min"
            }
        ]
        
        response_data = {
            "ok": True,
            "total_users": total_users,
            "active_users": active_users,
            "total_cards": total_cards,
            "users_count": total_users,
            "api_status": "online",
            "recent_activity": recent_activity
        }
        
        print(f"📊 Enviando respuesta: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return jsonify({
            "ok": False,
            "detail": str(e),
            "total_users": 0,
            "active_users": 0,
            "total_cards": 0,
            "users_count": 0,
            "api_status": "offline",
            "recent_activity": []
        }), 500

@app.get("/api/dashboard/system-info")
def api_dashboard_system_info():
    """Endpoint para información del sistema"""
    try:
        print("🔍 Solicitando información del sistema...")
        
        # Contar usuarios en DB
        db_users_count = users.count_documents({})
        
        # Verificar conexión a DB
        try:
            client.server_info()
            db_status = "connected"
            print(f"✅ DB conectada: {db_users_count} usuarios")
        except Exception as db_err:
            db_status = "disconnected"
            print(f"❌ DB desconectada: {db_err}")
        
        system_info = {
            "ok": True,
            "db_users_count": db_users_count,
            "db_status": db_status,
            "last_update": datetime.now(timezone.utc).isoformat(),
            "server_uptime": "99.9%",
            "memory_usage": "72%",
            "disk_space": "78%"
        }
        
        print(f"🔧 Info sistema: {system_info}")
        return jsonify(system_info)
        
    except Exception as e:
        print(f"❌ Error información sistema: {e}")
        return jsonify({
            "ok": False,
            "db_users_count": 0,
            "db_status": "disconnected",
            "last_update": datetime.now(timezone.utc).isoformat(),
            "detail": str(e)
        }), 500

@app.get("/api/dashboard/health")
def api_dashboard_health():
    """Endpoint para verificar la salud de la API"""
    start_time = datetime.now()
    
    try:
        print("🔍 Verificando salud del sistema...")
        
        # Verificar DB
        try:
            client.server_info()
            db_healthy = True
            user_count = users.count_documents({})
            print(f"✅ DB saludable: {user_count} usuarios")
        except Exception as db_err:
            db_healthy = False
            user_count = 0
            print(f"❌ DB no saludable: {db_err}")
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        health_data = {
            "ok": db_healthy,
            "database": db_healthy,
            "api": True,
            "user_count": user_count,
            "response_time": f"{response_time:.0f}",
            "version": "v1.0.0",
            "uptime": "99.9%",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        print(f"🏥 Health check: {health_data}")
        return jsonify(health_data)
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"❌ Error health check: {e}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "response_time": f"{response_time:.0f}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500
        


@app.get("/")
def root():
    return jsonify({"ok": True, "service": "Firefighter API", "status": "running"}), 200

if __name__ == "__main__":
    print("🚀 Auth API iniciando...")
    print(f"📊 Base de datos: {DB_NAME}")
    print(f"🔗 MongoDB URI: {MONGO_URI}")
    print("🌐 API corriendo en http://firefighter_backend:5000")
    
    # Crear usuario admin por defecto si no existe
    try:
        admin_exists = users.find_one({"username": "admin"})
        if not admin_exists:
            admin_doc = {
                "_id": str(uuid4()),
                "username": "admin",
                "email": "admin@firefighter.com",
                "password_hash": hash_password("admin123"),
                "created_at": datetime.now(timezone.utc),
                "role": "admin",
                "status": "active",
                "mfa_enabled": False,
                "mfa_secret": "",
                # Estructura embebida para admin
                "leitner_progress": {
                    "cards": [],
                    "stats": {
                        "total_cards": 0, "cards_by_box": {}, "last_study_session": None,
                        "total_reviews": 0, "correct_answers": 0, "accuracy_rate": 0.0,
                        "study_streak": 0, "cards_mastered": 0
                    },
                    "settings": {
                        "daily_goal": 20, "preferred_decks": [], "notification_enabled": True,
                        "study_reminders": "18:00", "auto_advance": True
                    },
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                "backoffice_cards": {
                    "cards": [], "total_cards": 0, "categories": [],
                    "created_at": datetime.now(timezone.utc),
                    "auto_populated": False
                }
            }
            users.insert_one(admin_doc)
            print("👤 Usuario admin creado con estructura embebida: admin/admin123")
    except Exception as e:
        print(f"⚠️ No se pudo crear usuario admin: {e}")
    
    app.run(host="0.0.0.0", port=5000, debug=True)
