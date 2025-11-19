#!/usr/bin/env python3
# clean_duplicate_null_cards.py - Limpiar registros NULL duplicados

import pymongo
from datetime import datetime, timezone

# Configuración
MONGO_USER = "joso"
MONGO_PASS = "XyGItdDKpWkfJfjT" 
MONGO_CLUSTER = "cluster0.yzzh9ig.mongodb.net"
DB_NAME = "FIREFIGHTER"

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Firefighter"

def clean_duplicate_nulls():
    try:
        print("🔍 Conectando a MongoDB...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        db = client[DB_NAME]
        leitner_cards = db["leitner_cards"]
        
        print(f"📊 Base de datos: {DB_NAME}")
        
        # Buscar registros con valores NULL que causan duplicados
        null_records = list(leitner_cards.find({
            "$or": [
                {"user": None},
                {"deck": None}, 
                {"front": None},
                {"user": ""},
                {"deck": ""},
                {"front": ""}
            ]
        }))
        
        print(f"🔍 Encontrados {len(null_records)} registros con valores NULL/vacíos")
        
        if len(null_records) == 0:
            print("✅ No hay registros NULL para limpiar")
            return
            
        # Mostrar algunos ejemplos
        print("📋 Ejemplos de registros problemáticos:")
        for i, record in enumerate(null_records[:3]):
            print(f"   {i+1}. _id: {record.get('_id')}")
            print(f"      user: {record.get('user')}")
            print(f"      deck: {record.get('deck')}")
            print(f"      front: {record.get('front')}")
            
        # Confirmar eliminación
        print(f"\n❓ ¿Eliminar {len(null_records)} registros con valores NULL? (y/N): ", end="")
        confirmacion = input().strip().lower()
        
        if confirmacion != 'y':
            print("❌ Operación cancelada")
            return
            
        # Eliminar registros NULL
        result = leitner_cards.delete_many({
            "$or": [
                {"user": None},
                {"deck": None}, 
                {"front": None},
                {"user": ""},
                {"deck": ""},
                {"front": ""}
            ]
        })
        
        print(f"✅ Eliminados {result.deleted_count} registros NULL")
        
        # Verificar estado final
        remaining_cards = leitner_cards.count_documents({})
        print(f"📋 Tarjetas restantes en leitner_cards: {remaining_cards}")
        
        # Mostrar tarjetas válidas
        valid_cards = list(leitner_cards.find({}).limit(5))
        if valid_cards:
            print("\n📋 Tarjetas válidas restantes:")
            for i, card in enumerate(valid_cards, 1):
                front = card.get('front', 'Sin título')
                user = card.get('user', 'Sin usuario')
                print(f"   {i}. {front[:40]}... (usuario: {user})")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    clean_duplicate_nulls()