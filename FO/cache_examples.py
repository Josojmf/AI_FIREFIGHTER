# FO/cache_examples.py - Ejemplos de cache para Frontend
"""
EJEMPLOS DE CACHE PARA FRONTEND
===============================
"""

from simple_memory_cache import cache_result

@cache_result(ttl=300, key_prefix="frontend")  # 5 minutos
def get_user_session_cached(session_id):
    """Session de usuario con cache"""
    # Tu codigo existente aqui
    return session_data

@cache_result(ttl=180, key_prefix="frontend")  # 3 minutos
def get_user_progress_cached(user_id):
    """Progreso de usuario con cache"""
    # Tu codigo existente aqui
    return progress_data
