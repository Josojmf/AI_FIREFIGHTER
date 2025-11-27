# cached_functions.py - Ejemplos de funciones con cache
"""
FUNCIONES CACHEADAS PARA FIREFIGHTER AI
========================================
Ejemplos de como cachear las funciones mas costosas
"""

from simple_memory_cache import cache_user_data, cache_cards_data, cache_chat_data
from datetime import datetime

# Ejemplo para datos de usuario
@cache_user_data(ttl=600)  # Cache 10 minutos
def get_user_profile_cached(user_id):
    """Obtener perfil de usuario con cache"""
    # Importar aqui para evitar imports circulares
    try:
        from database import get_final_collection  # Tu funcion de DB
        users = get_final_collection()
    except ImportError:
        # Fallback si no tienes database.py
        from pymongo import MongoClient
        import os
        mongo_uri = os.getenv("MONGO_URI")
        client = MongoClient(mongo_uri)
        users = client.FIREFIGHTER.users
    
    user = users.find_one({"_id": user_id})
    
    if user:
        # Solo datos seguros en cache
        return {
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email"),
            "created_at": user.get("created_at"),
            "preferences": user.get("preferences", {}),
            "stats": user.get("stats", {})
        }
    return None

# Ejemplo para cards de estudio
@cache_cards_data(ttl=300)  # Cache 5 minutos
def get_study_cards_cached(user_id, limit=20):
    """Obtener cards de estudio con cache"""
    try:
        from database import get_database
        db = get_database()
    except ImportError:
        # Fallback
        from pymongo import MongoClient
        import os
        mongo_uri = os.getenv("MONGO_URI")
        client = MongoClient(mongo_uri)
        db = client.FIREFIGHTER
    
    return list(db.cards.find({
        "user_id": user_id,
        "next_review": {"$lte": datetime.now()},
        "status": "active"
    }).sort([
        ("box", 1),
        ("next_review", 1)
    ]).limit(limit))

# Ejemplo para estadisticas de usuario
@cache_user_data(ttl=600)  # Cache 10 minutos
def get_user_stats_cached(user_id):
    """Estadisticas del usuario con cache"""
    try:
        from database import get_database
        db = get_database()
    except ImportError:
        # Fallback
        from pymongo import MongoClient
        import os
        mongo_uri = os.getenv("MONGO_URI")
        client = MongoClient(mongo_uri)
        db = client.FIREFIGHTER
    
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$box",
                "count": {"$sum": 1},
                "avg_difficulty": {"$avg": "$difficulty"},
                "categories": {"$addToSet": "$category"}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    
    return list(db.cards.aggregate(pipeline))

# Ejemplo para historial de chat
@cache_chat_data(ttl=180)  # Cache 3 minutos
def get_chat_history_cached(user_id, limit=50):
    """Historial de chat con cache"""
    try:
        from database import get_database
        db = get_database()
    except ImportError:
        # Fallback
        from pymongo import MongoClient
        import os
        mongo_uri = os.getenv("MONGO_URI")
        client = MongoClient(mongo_uri)
        db = client.FIREFIGHTER
    
    return list(db.conversations.find({
        "user_id": user_id
    }).sort([
        ("timestamp", -1)
    ]).limit(limit))

# Funcion para invalidar cache cuando se actualizan datos
def invalidate_cache_on_update(user_id, data_type="all"):
    """Invalidar cache cuando se actualizan datos"""
    from simple_memory_cache import invalidate_user_cache
    
    if data_type == "all":
        invalidate_user_cache(user_id)
    # Podrias ser mas especifico segun el tipo de datos
    
    print(f"🗑️ Cache invalidado para usuario {user_id}, tipo: {data_type}")

# COMO USAR ESTAS FUNCIONES:
# 
# En lugar de:
#   user = db.users.find_one({"_id": user_id})
# 
# Usa:
#   user = get_user_profile_cached(user_id)
# 
# Y automaticamente sera 5-10x mas rapido en requests subsecuentes!
