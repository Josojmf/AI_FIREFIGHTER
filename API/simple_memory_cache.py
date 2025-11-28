"""
Simple Memory Cache System for FirefighterAI
============================================
Sistema de cache en memoria thread-safe para optimización de performance
"""

import threading
import time
import hashlib
from typing import Any, Optional, Dict, Tuple
from functools import wraps

class SimpleMemoryCache:
    """Cache en memoria thread-safe con TTL y LRU"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
        print(f"✅ Caché inicializado (TTL: {default_ttl}s, Max: {max_size} entradas)")
    
    def _cleanup_expired(self):
        """Limpiar entradas expiradas"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if expiry < current_time
        ]
        
        for key in expired_keys:
            self.cache.pop(key, None)
            self.access_times.pop(key, None)
    
    def _evict_lru(self):
        """Eliminar entrada menos usada recientemente"""
        if not self.access_times:
            return
            
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        self.cache.pop(lru_key, None)
        self.access_times.pop(lru_key, None)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Establecer valor en cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        expiry_time = time.time() + ttl
        
        with self.lock:
            # Limpiar expirados
            self._cleanup_expired()
            
            # Evict si necesario
            while len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Añadir nueva entrada
            self.cache[key] = (value, expiry_time)
            self.access_times[key] = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        with self.lock:
            self._cleanup_expired()
            
            if key not in self.cache:
                return None
            
            value, expiry = self.cache[key]
            
            if expiry < time.time():
                # Expirado
                self.cache.pop(key, None)
                self.access_times.pop(key, None)
                return None
            
            # Actualizar tiempo de acceso
            self.access_times[key] = time.time()
            return value
    
    def delete(self, key: str) -> bool:
        """Eliminar entrada del cache"""
        with self.lock:
            if key in self.cache:
                self.cache.pop(key, None)
                self.access_times.pop(key, None)
                return True
            return False
    
    def clear(self) -> None:
        """Limpiar todo el cache"""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del cache"""
        with self.lock:
            self._cleanup_expired()
            
            total_entries = len(self.cache)
            usage_percent = (total_entries / self.max_size) * 100 if self.max_size > 0 else 0
            
            return {
                "total_entries": total_entries,
                "active_entries": total_entries,
                "expired_entries": 0,  # Ya limpiamos
                "max_size": self.max_size,
                "usage_percent": round(usage_percent, 1)
            }

# Instancia global del cache
memory_cache = SimpleMemoryCache()

def cache_result(ttl: int = 300, key_func=None):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave de cache
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Clave basada en función y argumentos
                func_name = f"{func.__module__}.{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = f"{func_name}:{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Intentar obtener del cache
            result = memory_cache.get(cache_key)
            if result is not None:
                return result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            memory_cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

def cache_user_data(ttl: int = 300):
    """Decorador específico para datos de usuario"""
    return cache_result(ttl=ttl, key_func=lambda user_id, *args, **kwargs: f"user:{user_id}")

def cache_cards_data(ttl: int = 180):
    """Decorador específico para datos de cards"""
    return cache_result(ttl=ttl, key_func=lambda user_id, *args, **kwargs: f"cards:{user_id}")

def cache_chat_data(ttl: int = 120):
    """Decorador específico para datos de chat"""
    return cache_result(ttl=ttl, key_func=lambda user_id, *args, **kwargs: f"chat:{user_id}")

def invalidate_user_cache(user_id: str) -> None:
    """Invalidar cache de usuario específico"""
    patterns = [f"user:{user_id}", f"cards:{user_id}", f"chat:{user_id}"]
    
    for pattern in patterns:
        memory_cache.delete(pattern)

def get_cache_stats() -> Dict[str, Any]:
    """Obtener estadísticas del cache"""
    return memory_cache.stats()

def clear_cache() -> None:
    """Limpiar todo el cache"""
    memory_cache.clear()

# Para compatibilidad con versiones anteriores
def cache_function(ttl=300):
    """Alias para cache_result"""
    return cache_result(ttl)
