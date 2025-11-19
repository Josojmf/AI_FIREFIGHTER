#!/usr/bin/env python3
"""
Script para insertar datos de prueba en las colecciones de FIREFIGHTER.
Incluye usuarios del BackOffice (Adm_Users).

Ejecutar localmente:
    python seed_database.py
"""

from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import bcrypt

# Credenciales
MONGO_USER = "joso"
MONGO_PASS = "XyGItdDKpWkfJfjT"
MONGO_CLUSTER = "cluster0.yzzh9ig.mongodb.net"
DB_NAME = "FIREFIGHTER"

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def main():
    # Construir URI
    uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Firefighter"
    
    print("🔗 Conectando a MongoDB Atlas...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        client.server_info()
        print("✅ Conectado exitosamente")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return
    
    db = client[DB_NAME]
    now = datetime.now(timezone.utc)
    
    # ========================================
    # 1. USUARIOS DEL BACKOFFICE (Adm_Users)
    # ========================================
    print("\n📋 Insertando usuarios del BackOffice (Adm_Users)...")
    adm_users = db["Adm_Users"]
    
    adm_users_data = [
        {
            "_id": str(uuid4()),
            "username": "admin",
            "email": "admin@firefighter.com",
            "password_hash": hash_password("admin123"),
            "created_at": now,
            "role": "admin",
            "status": "active",
            "mfa_enabled": False,
            "mfa_secret": ""
        }
    ]
    
    for user in adm_users_data:
        try:
            existing = adm_users.find_one({"username": user["username"]})
            if existing:
                print(f"   ⚠️  Usuario BackOffice '{user['username']}' ya existe, saltando...")
                continue
            adm_users.insert_one(user)
            print(f"   ✅ Usuario BackOffice '{user['username']}' creado")
        except Exception as e:
            print(f"   ❌ Error creando usuario BackOffice '{user['username']}': {e}")
    
    # ========================================
    # 2. USUARIOS PRINCIPALES (users)
    # ========================================
    print("\n📋 Insertando usuarios principales...")
    users = db["users"]
    
    users_data = [
        {
            "_id": str(uuid4()),
            "username": "admin",
            "email": "admin@firefighter.com",
            "password_hash": hash_password("admin123"),
            "created_at": now,
            "role": "admin",
            "status": "active",
            "mfa_enabled": False,
            "mfa_secret": ""
        },
        {
            "_id": str(uuid4()),
            "username": "bombero1",
            "email": "bombero1@firefighter.com",
            "password_hash": hash_password("bombero123"),
            "created_at": now,
            "role": "user",
            "status": "active",
            "mfa_enabled": False,
            "mfa_secret": ""
        },
        {
            "_id": str(uuid4()),
            "username": "bombero2",
            "email": "bombero2@firefighter.com",
            "password_hash": hash_password("bombero123"),
            "created_at": now,
            "role": "user",
            "status": "active",
            "mfa_enabled": False,
            "mfa_secret": ""
        }
    ]
    
    for user in users_data:
        try:
            existing = users.find_one({"username": user["username"]})
            if existing:
                print(f"   ⚠️  Usuario '{user['username']}' ya existe, saltando...")
                continue
            users.insert_one(user)
            print(f"   ✅ Usuario '{user['username']}' creado")
        except Exception as e:
            print(f"   ❌ Error creando usuario '{user['username']}': {e}")
    
    # ========================================
    # 3. TARJETAS LEITNER
    # ========================================
    print("\n📋 Insertando tarjetas Leitner...")
    leitner_cards = db["leitner_cards"]
    
    leitner_data = [
        # Tarjetas de equipamiento
        {
            "user": "admin",
            "deck": "equipamiento",
            "front": "¿Cuál es la presión mínima en línea de ataque?",
            "back": "3-5 bar según manguera/boquilla",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "equipamiento",
            "front": "¿Qué es un ERA?",
            "back": "Equipo de Respiración Autónomo - proporciona aire respirable en ambientes contaminados",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "equipamiento",
            "front": "¿Cuánto dura una botella de aire estándar?",
            "back": "Aproximadamente 30-45 minutos dependiendo del esfuerzo físico",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        # Tarjetas de procedimientos
        {
            "user": "admin",
            "deck": "procedimientos",
            "front": "¿Qué es el código MAYDAY?",
            "back": "MAYDAY MAYDAY MAYDAY + LUNAR (Localización, Unidad, Nombre, Asignación, Recursos necesarios)",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "procedimientos",
            "front": "¿Qué es la ventilación táctica?",
            "back": "Control de flujos de aire para evitar flashover, coordinado con el ataque",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "procedimientos",
            "front": "¿Qué es el RIT?",
            "back": "Rapid Intervention Team - equipo de rescate para bomberos en peligro",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        # Tarjetas de teoría del fuego
        {
            "user": "admin",
            "deck": "teoria",
            "front": "¿Cuáles son los elementos del triángulo del fuego?",
            "back": "Combustible + Oxígeno + Calor",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "teoria",
            "front": "¿Qué es un flashover?",
            "back": "Ignición simultánea de todos los materiales combustibles en un espacio cerrado",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "teoria",
            "front": "¿Qué es un backdraft?",
            "back": "Explosión causada por la entrada súbita de oxígeno en un espacio con gases calientes",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "teoria",
            "front": "¿Cuáles son las clases de fuego?",
            "back": "A (sólidos), B (líquidos), C (gases), D (metales), F (aceites de cocina)",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        # Tarjetas generales
        {
            "user": "admin",
            "deck": "general",
            "front": "¿Qué significa NFPA?",
            "back": "National Fire Protection Association",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        },
        {
            "user": "admin",
            "deck": "general",
            "front": "¿Cuál es el número de emergencias en España?",
            "back": "112",
            "box": 1,
            "due": now,
            "created_at": now,
            "history": []
        }
    ]
    
    # También crear tarjetas para bombero1
    for card in leitner_data.copy():
        new_card = card.copy()
        new_card["user"] = "bombero1"
        leitner_data.append(new_card)
    
    inserted_count = 0
    for card in leitner_data:
        try:
            existing = leitner_cards.find_one({
                "user": card["user"],
                "deck": card["deck"],
                "front": card["front"]
            })
            if existing:
                continue
            leitner_cards.insert_one(card)
            inserted_count += 1
        except Exception as e:
            if "duplicate" not in str(e).lower():
                print(f"   ❌ Error: {e}")
    
    print(f"   ✅ {inserted_count} tarjetas Leitner insertadas")
    
    # ========================================
    # RESUMEN FINAL
    # ========================================
    print("\n" + "="*50)
    print("📊 RESUMEN FINAL")
    print("="*50)
    
    collections = db.list_collection_names()
    for coll_name in sorted(collections):
        count = db[coll_name].count_documents({})
        print(f"   - {coll_name}: {count} documentos")
    
    print("\n✅ Base de datos poblada correctamente")
    print("\n🔑 Credenciales de acceso:")
    print("   BackOffice (Adm_Users):")
    print("   - admin / admin123")
    print("\n   Frontend (users):")
    print("   - admin / admin123 (rol: admin)")
    print("   - bombero1 / bombero123 (rol: user)")
    print("   - bombero2 / bombero123 (rol: user)")
    
    client.close()

if __name__ == "__main__":
    main()