# BO/cache_examples.py - Ejemplos de cache para BackOffice
"""
EJEMPLOS DE CACHE PARA BACKOFFICE
=================================
"""

from simple_memory_cache import cache_result

@cache_result(ttl=1800, key_prefix="admin")  # 30 minutos
def get_all_users_cached():
    """Todos los usuarios para admin (cacheado)"""
    # Tu codigo existente aqui
    return list(users.find({}))

@cache_result(ttl=600, key_prefix="admin")  # 10 minutos
def get_system_stats_cached():
    """Estadisticas del sistema (cacheado)"""
    # Tu codigo de stats aqui
    return {
        "total_users": users.count_documents({}),
        "total_cards": cards.count_documents({}),
        "active_sessions": sessions.count_documents({"active": True})
    }
