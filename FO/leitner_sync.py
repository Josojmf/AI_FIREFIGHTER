# leitner_sync.py - NUEVO: Sincronización con memory cards del BO

import requests
from datetime import datetime, timezone
from bson import ObjectId

def sync_memory_cards_to_leitner(username, cards_collection, api_base_url="http://localhost:5000", auth_token=None):
    """
    Sincroniza memory cards del BackOffice al sistema Leitner
    """
    try:
        print(f"🔄 Sincronizando memory cards para usuario: {username}")
        
        # Obtener memory cards desde la API del BO
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        response = requests.get(f"{api_base_url}/api/memory-cards", headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error obteniendo memory cards: {response.status_code}")
            return 0
            
        data = response.json()
        if not data.get('ok'):
            print(f"❌ API error: {data.get('detail', 'Unknown error')}")
            return 0
            
        memory_cards = data.get('cards', [])
        print(f"📋 Encontradas {len(memory_cards)} memory cards en el BO")
        
        # Sincronizar cada card
        synced_count = 0
        now = datetime.now(timezone.utc)
        
        for card in memory_cards:
            try:
                # Verificar si ya existe en Leitner
                existing = cards_collection.find_one({
                    "user": username,
                    "source_id": card['id'],
                    "source": "backoffice"
                })
                
                if existing:
                    # Actualizar si hay cambios
                    update_data = {}
                    if existing.get('front') != card['title']:
                        update_data['front'] = card['title']
                    if existing.get('back') != card['content']:
                        update_data['back'] = card['content']
                    if existing.get('category') != card.get('category', 'general'):
                        update_data['category'] = card.get('category', 'general')
                        
                    if update_data:
                        update_data['last_synced'] = now
                        cards_collection.update_one({"_id": existing["_id"]}, {"$set": update_data})
                        print(f"📝 Actualizada: {card['title'][:50]}...")
                        synced_count += 1
                else:
                    # Crear nueva carta Leitner
                    leitner_card = {
                        "user": username,
                        "deck": card.get('category', 'general'),
                        "front": card['title'],
                        "back": card['content'],
                        "box": 1,
                        "due": now,  # Disponible inmediatamente
                        "created_at": now,
                        "last_synced": now,
                        "source": "backoffice",
                        "source_id": card['id'],
                        "difficulty": card.get('difficulty', 'medium'),
                        "history": []
                    }
                    
                    cards_collection.insert_one(leitner_card)
                    print(f"➕ Creada: {card['title'][:50]}...")
                    synced_count += 1
                    
            except Exception as e:
                print(f"⚠️ Error procesando card {card.get('id')}: {e}")
                continue
                
        print(f"✅ Sincronización completada: {synced_count} tarjetas procesadas")
        return synced_count
        
    except Exception as e:
        print(f"❌ Error en sincronización: {e}")
        return 0

def create_memory_card_from_leitner(leitner_card, api_base_url="http://localhost:5000", auth_token=None):
    """
    Crea una memory card en el BO desde una carta Leitner
    """
    try:
        headers = {'Content-Type': 'application/json'}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
            
        card_data = {
            "title": leitner_card.get('front', ''),
            "content": leitner_card.get('back', ''),
            "category": leitner_card.get('deck', 'general'),
            "difficulty": leitner_card.get('difficulty', 'medium')
        }
        
        response = requests.post(
            f"{api_base_url}/api/memory-cards",
            json=card_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            if data.get('ok'):
                return data.get('card', {}).get('id')
                
        return None
        
    except Exception as e:
        print(f"❌ Error creando memory card: {e}")
        return None

# Agregar endpoint de sincronización al leitner.py
@leitner_bp.route("/api/leitner/sync", methods=["POST"])
@login_required_bp
def api_sync_memory_cards():
    """
    Endpoint para sincronizar memory cards del BO al sistema Leitner
    """
    username = session.get("user")
    cards_col = get_cards_collection()
    
    if not cards_col:
        return jsonify({"ok": False, "detail": "Base de datos no disponible"}), 500
        
    # TODO: Obtener token de autenticación desde la sesión
    auth_token = session.get('api_token')  # Necesitarás configurar esto
    
    try:
        synced_count = sync_memory_cards_to_leitner(
            username, 
            cards_col, 
            api_base_url="http://localhost:5000",  # URL de tu API
            auth_token=auth_token
        )
        
        return jsonify({
            "ok": True, 
            "synced": synced_count,
            "message": f"Sincronizadas {synced_count} tarjetas correctamente"
        })
        
    except Exception as e:
        return jsonify({"ok": False, "detail": str(e)}), 500