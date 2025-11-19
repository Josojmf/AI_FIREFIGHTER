#!/usr/bin/env python3
# insert-admin-fixed.py - Script para crear usuario admin correctamente

import bcrypt
import os
import sys
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def create_admin_user():
    # Configuración MongoDB
    MONGO_USER = os.getenv("MONGO_USER", "joso")
    MONGO_PASS = os.getenv("MONGO_PASS", "XyGItdDKpWkfJfjT")
    MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.yzzh9ig.mongodb.net")
    DB_NAME = os.getenv("DB_NAME", "FIREFIGHTER")

    # URI de conexión
    uri = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{DB_NAME}?retryWrites=true&w=majority"
    
    try:
        print("🔗 Conectando a MongoDB...")
        client = MongoClient(uri, serverSelectionTimeoutMS=10000)
        
        # Probar conexión
        client.server_info()
        print("✅ Conectado a MongoDB exitosamente")
        
        # Obtener colección correcta
        db = client[DB_NAME]
        # IMPORTANTE: La API usa la colección 'users', no 'Adm_Users'
        users_collection = db["users"]
        
        print(f"📊 Usando colección: {users_collection.name}")
        print(f"📋 Documentos existentes: {users_collection.count_documents({})}")
        
        # Datos del admin
        admin_email = "admin@firefighter.com"
        admin_username = "admin"
        admin_password = "admin123"  # Cambiar en producción
        
        # Generar hash bcrypt
        print("🔒 Generando hash de contraseña...")
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(admin_password.encode("utf-8"), salt).decode("utf-8")
        
        # Documento del usuario admin
        admin_doc = {
            "username": admin_username,
            "email": admin_email,
            "password_hash": password_hash,
            "role": "admin",  # ¡CRÍTICO para backoffice!
            "mfa_enabled": False,
            "mfa_secret": None,
            "status": "active",
            "created_at": datetime.utcnow(),
            "last_login": None,
            "profile": {
                "full_name": "Administrador",
                "department": "IT",
                "phone": "+34 600 000 000"
            }
        }
        
        print("👤 Insertando/actualizando usuario admin...")
        
        # Usar upsert para crear o actualizar
        result = users_collection.find_one_and_update(
            {"$or": [{"email": admin_email}, {"username": admin_username}]},
            {"$set": admin_doc},
            upsert=True,
            return_document=True
        )
        
        print("✅ Usuario admin creado/actualizado exitosamente!")
        print(f"📋 ID: {result.get('_id')}")
        print(f"👤 Username: {result.get('username')}")
        print(f"📧 Email: {result.get('email')}")
        print(f"🛡️ Role: {result.get('role')}")
        print(f"🔐 MFA: {'Habilitado' if result.get('mfa_enabled') else 'Deshabilitado'}")
        
        # Verificar otros usuarios admin
        admin_count = users_collection.count_documents({"role": "admin"})
        print(f"📊 Total de administradores: {admin_count}")
        
        print("\n🔑 CREDENCIALES PARA LOGIN:")
        print(f"   Username: {admin_username}")
        print(f"   Password: {admin_password}")
        print("   ⚠️  CAMBIAR PASSWORD EN PRODUCCIÓN")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        try:
            client.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 FirefighterAI - Creador de Usuario Admin")
    print("=" * 50)
    
    success = create_admin_user()
    
    if success:
        print("\n✅ ¡Proceso completado exitosamente!")
        print("🌐 Ahora puedes hacer login en el backoffice")
        sys.exit(0)
    else:
        print("\n❌ Error durante el proceso")
        sys.exit(1)