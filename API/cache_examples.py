# API/cache_examples.py - Ejemplos de cache para API
"""
EJEMPLOS DE CACHE PARA API BACKEND
==================================
"""

from simple_memory_cache import cache_user_data, cache_cards_data
from datetime import datetime

@cache_user_data(ttl=600)  # 10 minutos
def get_user_by_id_cached(user_id):
    """Usuario por ID con cache"""
    # Tu codigo existente aqui
    user = users.find_one({"_id": user_id})
    return user

@cache_cards_data(ttl=300)  # 5 minutos  
def get_study_cards_cached(user_id, limit=20):
    """Cards de estudio con cache"""
    # Tu codigo existente aqui
    cards = db.cards.find({
        "user_id": user_id,
        "next_review": {"$lte": datetime.now()},
        "status": "active"
    }).sort([("box", 1)]).limit(limit)
    return list(cards)

@cache_user_data(ttl=900)  # 15 minutos
def get_user_stats_cached(user_id):
    """Stats de usuario con cache"""
    # Tu aggregation pipeline aqui
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {"_id": "$box", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    return list(db.cards.aggregate(pipeline))
