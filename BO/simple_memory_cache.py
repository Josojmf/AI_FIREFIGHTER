# simple_memory_cache.py - Sistema de caché en memoria ultra-simple
"""
CACHÉ EN MEMORIA SIMPLE - MÁXIMO IMPACTO
=========================================
Sistema de caché ultra-simple que mejora performance inmediatamente
"""

import time
import json
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock

class SimpleMemoryCache:
    """Caché en memoria thread-safe y ultra-simple"""
    
    def __init__(self, default_ttl=300, max_size=1000):
        """
        Inicializar caché
        default_ttl: tiempo de vida por defecto (segundos)
        max_size: máximo número de entradas
        """
        self.cache = {}
        self.ttl_data = {}
        self.access_times = {}  # Para LRU
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.lock = Lock()
        
        print(f"✅ Caché inicializado (TTL: {default_ttl}s, Max: {max_size} entradas)")
    
    def _is_expired(self, key):
        """Verificar si una entrada ha expirado"""
        if key not in self.ttl_data:
            return True
        return time.time() > self.ttl_data[key]
    
    def _cleanup_expired(self):
        """Limpiar entradas expiradas"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self.ttl_data.items() 
            if current_time > expiry
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.ttl_data.pop(key, None)
            self.access_times.pop(key, None)
        
        if expired_keys:
            print(f"🗑️ Cache cleanup: {len(expired_keys)} entradas expiradas eliminadas")
    
    def _enforce_max_size(self):
        """Aplicar límite de tamaño usando LRU"""
        if len(self.cache) <= self.max_size:
            return
        
        # Eliminar entradas menos usadas
        entries_to_remove = len(self.cache) - self.max_size + 10  # Remover 10 extras
        
        # Ordenar por tiempo de acceso (LRU)
        lru_keys = sorted(
            self.access_times.keys(),
            key=lambda k: self.access_times[k]
        )[:entries_to_remove]
        
        for key in lru_keys:
            self.cache.pop(key, None)
            self.ttl_data.pop(key, None)
            self.access_times.pop(key, None)
        
        print(f"📏 Cache size limit: {entries_to_remove} entradas LRU eliminadas")
    
    def get(self, key):
        """Obtener valor del caché"""
        with self.lock:
            if key in self.cache and not self._is_expired(key):
                self.access_times[key] = time.time()  # Actualizar LRU
                return self.cache[key]
            
            # Si existe pero expiró, eliminarlo
            if key in self.cache:
                self.cache.pop(key, None)
                self.ttl_data.pop(key, None)
                self.access_times.pop(key, None)
        
        return None
    
    def set(self, key, value, ttl=None):
        """Guardar valor en caché"""
        if ttl is None:
            ttl = self.default_ttl
        
        with self.lock:
            # Limpiar expirados ocasionalmente
            if len(self.cache) % 50 == 0:
                self._cleanup_expired()
            
            # Guardar en caché
            self.cache[key] = value
            self.ttl_data[key] = time.time() + ttl
            self.access_times[key] = time.time()
            
            # Aplicar límite de tamaño
            self._enforce_max_size()
    
    def delete(self, key):
        """Eliminar entrada del caché"""
        with self.lock:
            self.cache.pop(key, None)
            self.ttl_data.pop(key, None)
            self.access_times.pop(key, None)
    
    def clear(self):
        """Limpiar todo el caché"""
        with self.lock:
            self.cache.clear()
            self.ttl_data.clear()
            self.access_times.clear()
        print("🗑️ Caché completamente limpiado")
    
    def stats(self):
        """Obtener estadísticas del caché"""
        with self.lock:
            current_time = time.time()
            active_entries = sum(
                1 for expiry in self.ttl_data.values() 
                if current_time <= expiry
            )
            
            return {
                "total_entries": len(self.cache),
                "active_entries": active_entries,
                "expired_entries": len(self.cache) - active_entries,
                "max_size": self.max_size,
                "usage_percent": len(self.cache) / self.max_size * 100
            }

# Instancia global del caché
memory_cache = SimpleMemoryCache(default_ttl=300, max_size=1000)

# Decoradores para facilitar el uso
def cache_result(ttl=300, key_prefix=""):
    """
    Decorador para cachear resultados de funciones
    
    @cache_result(ttl=600, key_prefix="user_data")
    def get_user_profile(user_id):
        return expensive_database_query(user_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de caché
            args_str = str(args) + str(sorted(kwargs.items()))
            key_hash = hashlib.md5(args_str.encode()).hexdigest()[:10]
            cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"
            
            # Intentar obtener del caché
            cached_result = memory_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear
            result = func(*args, **kwargs)
            memory_cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def cache_user_data(ttl=600):
    """Decorador específico para datos de usuario"""
    return cache_result(ttl=ttl, key_prefix="user")

def cache_cards_data(ttl=300):
    """Decorador específico para datos de cards"""
    return cache_result(ttl=ttl, key_prefix="cards")

def cache_chat_data(ttl=180):
    """Decorador específico para datos de chat"""
    return cache_result(ttl=ttl, key_prefix="chat")

# Funciones de utilidad para Flask
def invalidate_user_cache(user_id):
    """Invalidar caché relacionado con un usuario específico"""
    keys_to_delete = []
    
    with memory_cache.lock:
        for key in memory_cache.cache.keys():
            if f"user_id_{user_id}" in key or f":{user_id}:" in key:
                keys_to_delete.append(key)
    
    for key in keys_to_delete:
        memory_cache.delete(key)
    
    if keys_to_delete:
        print(f"🗑️ Invalidado caché para usuario {user_id}: {len(keys_to_delete)} entradas")

def get_cache_stats():
    """Obtener estadísticas del caché para monitoring"""
    return memory_cache.stats()

# ========================================
# EJEMPLOS DE USO EN TU APLICACIÓN
# ========================================

# Ejemplo 1: Cachear perfil de usuario
@cache_user_data(ttl=600)  # 10 minutos
def get_user_profile(user_id):
    """Obtener perfil de usuario (cacheado)"""
    from app import db  # Tu conexión a DB
    
    user = db.users.find_one({"_id": user_id})
    if user:
        # Solo cachear datos seguros (sin passwords)
        safe_user = {
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
            "preferences": user.get("preferences", {}),
            "stats": user.get("stats", {})
        }
        return safe_user
    return None

# Ejemplo 2: Cachear estadísticas de cards
@cache_cards_data(ttl=300)  # 5 minutos
def get_user_card_stats(user_id):
    """Estadísticas de cards del usuario (cacheado)"""
    from app import db
    
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

# Ejemplo 3: Cachear cards de estudio
@cache_cards_data(ttl=180)  # 3 minutos
def get_study_cards(user_id, limit=20):
    """Cards de estudio para el usuario (cacheado)"""
    from app import db
    from datetime import datetime
    
    return list(db.cards.find({
        "user_id": user_id,
        "next_review": {"$lte": datetime.now()},
        "status": "active"
    }).sort([
        ("box", 1), 
        ("next_review", 1)
    ]).limit(limit))

# Ejemplo 4: Cachear historial de chat
@cache_chat_data(ttl=120)  # 2 minutos
def get_chat_history(user_id, limit=50):
    """Historial de chat del usuario (cacheado)"""
    from app import db
    
    return list(db.conversations.find({
        "user_id": user_id
    }).sort([
        ("timestamp", -1)
    ]).limit(limit))

# ========================================
# INTEGRACIÓN CON FLASK
# ========================================

def init_cache_for_flask(app):
    """Inicializar caché para Flask app"""
    
    @app.before_request
    def setup_cache_context():
        """Hacer caché disponible en contexto Flask"""
        from flask import g
        g.cache = memory_cache
    
    @app.route('/api/cache/stats')
    def cache_stats_endpoint():
        """Endpoint para ver estadísticas del caché"""
        from flask import jsonify
        return jsonify(get_cache_stats())
    
    @app.route('/api/cache/clear', methods=['POST'])
    def clear_cache_endpoint():
        """Endpoint para limpiar caché (admin only)"""
        from flask import jsonify
        # TODO: Agregar verificación de admin
        memory_cache.clear()
        return jsonify({"message": "Cache cleared successfully"})
    
    print("✅ Caché integrado con Flask")

# ========================================
# MONITORING Y DEBUGGING
# ========================================

def print_cache_stats():
    """Imprimir estadísticas del caché"""
    stats = memory_cache.stats()
    
    print(f"\n📊 ESTADÍSTICAS DEL CACHÉ:")
    print(f"   💾 Entradas totales: {stats['total_entries']}")
    print(f"   ✅ Entradas activas: {stats['active_entries']}")
    print(f"   ⏰ Entradas expiradas: {stats['expired_entries']}")
    print(f"   📏 Uso del espacio: {stats['usage_percent']:.1f}%")
    print(f"   📊 Límite máximo: {stats['max_size']}")

def monitor_cache_performance():
    """Monitor simple de performance del caché"""
    import threading
    import time
    
    def monitor_loop():
        while True:
            time.sleep(60)  # Cada minuto
            stats = memory_cache.stats()
            
            if stats['usage_percent'] > 90:
                print(f"⚠️ Caché casi lleno: {stats['usage_percent']:.1f}%")
            
            if stats['expired_entries'] > stats['active_entries']:
                print(f"🗑️ Muchas entradas expiradas, limpiando...")
                memory_cache._cleanup_expired()
    
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    print("📊 Monitor de caché iniciado")

if __name__ == "__main__":
    # Test del caché
    print("🧪 TESTING DEL CACHÉ...")
    
    # Test básico
    memory_cache.set("test_key", "test_value", ttl=5)
    print(f"Test get: {memory_cache.get('test_key')}")
    
    # Test de expiración
    time.sleep(6)
    print(f"Test expired: {memory_cache.get('test_key')}")
    
    # Test de estadísticas
    print_cache_stats()
    
    print("✅ Caché funcionando correctamente")