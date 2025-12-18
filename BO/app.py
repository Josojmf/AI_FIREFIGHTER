# run_waitress.py
import os
import sys

# Configurar entorno
os.environ["WERKZEUG_RUN_MAIN"] = "true"

# Añadir el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from waitress import serve
from app import create_app
# Cache en memoria para BackOffice
from simple_memory_cache import memory_cache, cache_result, get_cache_stats


app = create_app()

if __name__ == '__main__':
    print("🚀 Firefighter Backoffice iniciando con Waitress...")
    print("🌐 Panel de administración: http://localhost:8080")
    
    api_url = 'http://localhost:5000'
    print(f"🔗 Conectado a API: {api_url}")
    print("✅ Servidor iniciado correctamente!")
    
    # Usar Waitress en lugar de Flask dev server
    serve(app, host='0.0.0.0', port=8080, threads=4)
