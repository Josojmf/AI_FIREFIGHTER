#!/usr/bin/env python3
# set_cards_due_future.py - Establecer todas las leitner_cards como due en el futuro

import pymongo
from datetime import datetime, timedelta, timezone
from bson import ObjectId
import sys

# Configuración
MONGO_USER = "joso"
MONGO_PASS = "XyGItdDKpWkfJfjT" 
MONGO_CLUSTER = "cluster0.yzzh9ig.mongodb.net"
DB_NAME = "FIREFIGHTER"
COLLECTION_NAME = "leitner_cards"
DAYS_FUTURE = 30  # Cambiar este valor para diferentes períodos

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=Firefighter"

def main():
    try:
        print("🔍 Conectando a MongoDB...")
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        client.server_info()  # Test conexión
        
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        print(f"📊 Base de datos: {DB_NAME}")
        print(f"🗃️ Colección: {COLLECTION_NAME}")
        
        # Contar documentos
        total_cards = collection.count_documents({})
        print(f"📋 Total tarjetas encontradas: {total_cards}")
        
        if total_cards == 0:
            print("⚠️ No hay tarjetas en la colección")
            return
        
        # Mostrar estado actual
        print("\n📊 Estado actual de las tarjetas:")
        now_utc = datetime.now(timezone.utc)
        
        # Contar vencidas y futuras
        due_cards = collection.count_documents({"due": {"$lte": now_utc}})
        future_cards = collection.count_documents({"due": {"$gt": now_utc}})
        
        print(f"   ⏰ Vencidas ahora: {due_cards}")
        print(f"   📅 Futuras: {future_cards}")
        print(f"   📋 Sin fecha due: {total_cards - due_cards - future_cards}")
        
        # Calcular nueva fecha due (en el futuro)
        future_due = now_utc + timedelta(days=DAYS_FUTURE)
        
        print(f"\n🕐 Tiempo actual: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📅 Nueva fecha due: {future_due.strftime('%Y-%m-%d %H:%M:%S UTC')} ({DAYS_FUTURE} días en el futuro)")
        
        # Confirmar operación
        print(f"\n❓ ¿Establecer TODAS las {total_cards} tarjetas para vencer en {DAYS_FUTURE} días? (y/N): ", end="")
        confirmacion = input().strip().lower()
        
        if confirmacion != 'y':
            print("❌ Operación cancelada")
            return
        
        # Actualizar TODAS las tarjetas
        print("\n🔄 Actualizando todas las tarjetas...")
        
        result = collection.update_many(
            {},  # Filtro vacío = todas las tarjetas
            {
                "$set": {
                    "due": future_due,
                    "updated_by_script": now_utc,
                    "script_action": f"set_due_future_{DAYS_FUTURE}_days"
                }
            }
        )
        
        print(f"\n✅ Operación completada:")
        print(f"   📝 Tarjetas modificadas: {result.modified_count}")
        print(f"   📋 Tarjetas encontradas: {result.matched_count}")
        
        if result.modified_count > 0:
            print(f"\n🎉 ¡Éxito! Todas las tarjetas ahora vencerán el {future_due.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # Verificar resultado
            print("\n🔍 Verificando tarjetas actualizadas:")
            sample_cards = list(collection.find({}).limit(5))
            for i, card in enumerate(sample_cards, 1):
                front = card.get('front', card.get('title', 'Sin título'))
                due_date = card.get('due')
                if due_date:
                    due_str = due_date.strftime('%Y-%m-%d %H:%M:%S UTC') if hasattr(due_date, 'strftime') else str(due_date)
                else:
                    due_str = 'Sin fecha'
                print(f"   {i}. {front[:40]}... | Due: {due_str}")
                
            print(f"\n📊 Nuevo estado:")
            due_cards_new = collection.count_documents({"due": {"$lte": now_utc}})
            future_cards_new = collection.count_documents({"due": {"$gt": now_utc}})
            print(f"   ⏰ Vencidas ahora: {due_cards_new}")
            print(f"   📅 Futuras: {future_cards_new}")
            
        else:
            print("⚠️ No se modificaron tarjetas")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Función adicional para establecer tarjetas como vencidas AHORA
def set_cards_due_now():
    """Establecer todas las tarjetas como vencidas (para estudio inmediato)"""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        db = client[DB_NAME]
        collection = db[COLLECTION_NAME]
        
        now_utc = datetime.now(timezone.utc)
        past_due = now_utc - timedelta(minutes=5)  # 5 minutos en el pasado
        
        print(f"🔄 Estableciendo todas las tarjetas como vencidas...")
        
        result = collection.update_many(
            {},
            {
                "$set": {
                    "due": past_due,
                    "updated_by_script": now_utc,
                    "script_action": "set_due_now"
                }
            }
        )
        
        print(f"✅ {result.modified_count} tarjetas ahora están vencidas (disponibles para estudio)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 Opciones:")
    print("   1. Establecer tarjetas para vencer en el FUTURO (30 días)")
    print("   2. Establecer tarjetas como vencidas AHORA (para estudio)")
    print("   3. Salir")
    
    opcion = input("\nElige una opción (1/2/3): ").strip()
    
    if opcion == "1":
        main()
    elif opcion == "2":
        set_cards_due_now()
    else:
        print("👋 ¡Hasta luego!")