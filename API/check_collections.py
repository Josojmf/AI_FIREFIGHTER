import requests
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración MongoDB
MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS") 
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER", "cluster0.yzzh9ig.mongodb.net")
DB_NAME = os.getenv("DB_NAME", "FIREFIGHTER")

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/?retryWrites=true&w=majority&appName=FirefighterAPI"

def check_collections():
    """Verificar qué colecciones existen y cuál tiene las memory cards"""
    try:
        print("🔍 Conectando a MongoDB...")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
        db = client[DB_NAME]
        
        print(f"📊 Base de datos: {DB_NAME}")
        print(f"🔗 Cluster: {MONGO_CLUSTER}")
        
        # Listar todas las colecciones
        collections = db.list_collection_names()
        print(f"\n📋 Colecciones encontradas: {len(collections)}")
        for coll_name in collections:
            count = db[coll_name].count_documents({})
            print(f"  - {coll_name}: {count} documentos")
        
        # Verificar específicamente las colecciones que nos interesan
        print(f"\n🔍 Verificando colecciones específicas:")
        
        target_collections = ['leitner_cards', 'memory_cards', 'Adm_Users', 'cards']
        for coll_name in target_collections:
            if coll_name in collections:
                count = db[coll_name].count_documents({})
                print(f"  ✅ {coll_name}: {count} documentos")
                
                # Mostrar algunos documentos de ejemplo
                if count > 0:
                    sample = list(db[coll_name].find().limit(3))
                    for i, doc in enumerate(sample):
                        # Mostrar solo los campos principales
                        fields = {k: v for k, v in doc.items() if k in ['_id', 'title', 'content', 'category', 'difficulty']}
                        print(f"    Ejemplo {i+1}: {fields}")
            else:
                print(f"  ❌ {coll_name}: No existe")
        
        print(f"\n🎯 Recomendación:")
        # Buscar la colección con más documentos que parezcan memory cards
        max_count = 0
        best_collection = None
        
        for coll_name in collections:
            if any(keyword in coll_name.lower() for keyword in ['card', 'leitner', 'memory']):
                count = db[coll_name].count_documents({})
                if count > max_count:
                    max_count = count
                    best_collection = coll_name
        
        if best_collection:
            print(f"  La colección '{best_collection}' tiene {max_count} documentos y parece ser la correcta")
        else:
            print("  No se encontró una colección clara para memory cards")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_api_cards():
    """Probar la API para ver qué devuelve"""
    try:
        print("\n🔍 Probando API de memory cards...")
        
        # Primero login para obtener token
        login_response = requests.post(
            "http://localhost:5000/api/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            token = login_data.get('access_token')
            
            # Ahora obtener memory cards
            headers = {'Authorization': f'Bearer {token}'}
            cards_response = requests.get(
                "http://localhost:5000/api/memory-cards",
                headers=headers,
                timeout=10
            )
            
            print(f"📡 API Response: {cards_response.status_code}")
            if cards_response.status_code == 200:
                data = cards_response.json()
                cards = data.get('cards', [])
                print(f"🃏 Cards encontradas via API: {len(cards)}")
                
                # Mostrar algunas cards de ejemplo
                for i, card in enumerate(cards[:3]):
                    print(f"  Card {i+1}: ID={card.get('id')}, Title={card.get('title', 'Sin título')}")
                    
            else:
                print(f"❌ Error API: {cards_response.text}")
        else:
            print(f"❌ Error login: {login_response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_collections()
    test_api_cards()