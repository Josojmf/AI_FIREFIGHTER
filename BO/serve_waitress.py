"""
Serve Waitress - Production Server for Backoffice
==================================================
Optimizado para Docker Swarm y Digital Ocean
"""

from waitress import serve
import os
import socket
from app import create_app

# Configuración para producción
os.environ['FLASK_ENV'] = 'production'
os.environ['ENVIRONMENT'] = 'production'
os.environ['DOCKER'] = 'true'

# Crear la aplicación Flask
app = create_app()

if __name__ == "__main__":
    # Obtener configuración de entorno
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3001"))
    threads = int(os.getenv("WAITRESS_THREADS", "10"))
    
    # Info del host
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    
    print("=" * 70)
    print("🚀 FIREFIGHTER BACKOFFICE - PRODUCTION MODE")
    print("=" * 70)
    print(f"🐋 Docker/Swarm: YES")
    print(f"🌐 Hostname: {hostname}")
    print(f"📍 IP: {ip}")
    print(f"📡 Escuchando en: {host}:{port}")
    print(f"🧵 Threads: {threads}")
    print(f"🔗 API URL: {app.config.get('API_BASE_URL', 'Not set')}")
    print("=" * 70)
    print("✅ Servidor iniciado correctamente!")
    print("=" * 70)
    
    # Configuración optimizada para producción
    serve(
        app,
        host=host,
        port=port,
        threads=threads,
        connection_limit=1000,
        channel_timeout=60,
        cleanup_interval=30,
        asyncore_use_poll=True,
        url_scheme='https' if app.config.get('SESSION_COOKIE_SECURE') else 'http'
    )