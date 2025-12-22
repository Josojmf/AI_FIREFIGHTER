"""
Serve Waitress - Production Server Optimizado
Versión ultra robusta con manejo de señales, graceful shutdown y healthchecks
"""
from waitress import serve
import os
import sys
import signal
import socket
import time
import traceback
from threading import Thread
from datetime import datetime

# Configurar entorno para producción
os.environ['FLASK_ENV'] = 'production'
os.environ['ENVIRONMENT'] = 'production'
os.environ['DOCKER'] = 'true'

def create_app_with_fallback():
    """Crear aplicación con múltiples fallbacks"""
    try:
        from app import create_app
        return create_app()
    except Exception as app_error:  # <-- NOMBRE DE VARIABLE CAMBIADO
        print(f"💀 ERROR creando aplicación: {app_error}")
        traceback.print_exc()
        
        # Aplicación de emergencia mínima
        from flask import Flask
        emergency_app = Flask(__name__)
        
        @emergency_app.route('/')
        def emergency_root():
            """Página raíz de emergencia"""
            error_msg = str(app_error) if app_error else "Unknown error"  # <-- USAR app_error
            return f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>⚠️ Firefighter BackOffice - Emergency Mode</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 50px; line-height: 1.6; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; border: 2px solid #ff6b6b; border-radius: 10px; background: #fff5f5; }}
                    h1 {{ color: #d63031; }}
                    .error {{ background: #ffeaa7; padding: 15px; border-radius: 5px; font-family: monospace; }}
                    .actions {{ margin-top: 20px; }}
                    .btn {{ display: inline-block; padding: 10px 20px; background: #0984e3; color: white; text-decoration: none; border-radius: 5px; margin-right: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>⚠️ Firefighter BackOffice - Emergency Mode</h1>
                    <p>The application failed to start properly. The system is running in emergency mode.</p>
                    
                    <div class="error">
                        <strong>Error:</strong> {error_msg}
                    </div>
                    
                    <div class="actions">
                        <a href="/health" class="btn">Check Health</a>
                        <a href="/debug" class="btn">Debug Info</a>
                    </div>
                    
                    <h3>Next Steps:</h3>
                    <ol>
                        <li>Check the server logs for detailed error information</li>
                        <li>Verify environment variables are correctly set</li>
                        <li>Ensure all dependencies are installed</li>
                        <li>Restart the service</li>
                    </ol>
                    
                    <p><small>Service started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
                </div>
            </body>
            </html>
            """, 500
        
        @emergency_app.route('/health')
        def emergency_health():
            """Health check de emergencia"""
            error_msg = str(app_error) if app_error else "Unknown error"  # <-- USAR app_error
            return {
                'status': 'emergency',
                'service': 'backoffice',
                'timestamp': datetime.now().isoformat(),
                'mode': 'emergency_fallback',
                'error': error_msg,
                'endpoints': {
                    'health': '/health',
                    'debug': '/debug',
                    'info': '/server/info'
                }
            }, 503
        
        @emergency_app.route('/debug')
        def emergency_debug():
            """Debug endpoint de emergencia"""
            import platform
            
            debug_info = {
                'python_version': platform.python_version(),
                'platform': platform.platform(),
                'hostname': socket.gethostname(),
                'pid': os.getpid(),
                'environment': dict(os.environ),
                'sys_path': sys.path,
                'current_dir': os.getcwd(),
                'files_in_app': os.listdir('.') if os.path.exists('.') else [],
            }
            
            # Ocultar valores sensibles
            for key in list(debug_info['environment'].keys()):
                if any(sensitive in key.lower() for sensitive in ['key', 'secret', 'password', 'token']):
                    value = debug_info['environment'][key]
                    if value:
                        debug_info['environment'][key] = f"***{value[-4:]}" if len(value) > 4 else "***"
            
            return debug_info
        
        return emergency_app

class HealthMonitor:
    """Monitor de salud del servidor"""
    
    def __init__(self, port=3001):
        self.port = port
        self.running = True
        self.health_status = 'starting'
        self.start_time = time.time()
        self.request_count = 0
    
    def check_health(self):
        """Verificar salud del servidor"""
        try:
            # Intentar conectar al puerto local
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', self.port))
            sock.close()
            
            if result == 0:
                self.health_status = 'healthy'
                return True
            else:
                self.health_status = 'unreachable'
                return False
        except Exception as e:
            self.health_status = f'error: {e}'
            return False
    
    def get_status(self):
        """Obtener estado completo"""
        uptime = time.time() - self.start_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            'status': self.health_status,
            'uptime': f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
            'port': self.port,
            'requests': self.request_count,
            'timestamp': datetime.now().isoformat(),
            'service': 'backoffice'
        }
    
    def increment_requests(self):
        """Incrementar contador de requests"""
        self.request_count += 1

class GracefulShutdown:
    """Manejo de shutdown graceful"""
    
    def __init__(self):
        self.should_exit = False
        self.exit_code = 0
        
        # Registrar manejadores de señales
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)
    
    def handle_signal(self, signum, frame):
        """Manejar señales de terminación"""
        signal_name = signal.Signals(signum).name if hasattr(signal.Signals, 'name') else str(signum)
        print(f"\n⚠️  Recibida señal {signal_name}")
        self.should_exit = True
        self.exit_code = 0 if signum == signal.SIGTERM else 130
    
    def should_stop(self):
        """Verificar si debería detenerse"""
        return self.should_exit

def print_banner(app, host, port, threads):
    """Mostrar banner informativo"""
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
    except:
        hostname = "unknown"
        ip = "unknown"
    
    print("=" * 70)
    print("🚀 FIREFIGHTER BACKOFFICE - PRODUCTION SERVER")
    print("=" * 70)
    print(f"🐋 Docker/Swarm Mode:    ENABLED")
    print(f"🌐 Hostname:             {hostname}")
    print(f"📍 IP Address:           {ip}")
    print(f"📡 Listening:            {host}:{port}")
    print(f"🧵 Threads:              {threads}")
    print(f"🔧 Environment:          production")
    print(f"📊 Log Level:            INFO")
    print(f"🕐 Started:              {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print("📝 Commands:")
    print("   Ctrl+C - Graceful shutdown")
    print("   SIGTERM - Graceful shutdown")
    print("   SIGKILL - Force shutdown (not recommended)")
    print("=" * 70)
    
    # Mostrar configuración de la app
    try:
        api_url = app.config.get('API_BASE_URL', 'Not set')
        print(f"🔗 API URL: {api_url}")
        print(f"🍪 Session Cookie: {app.config.get('SESSION_COOKIE_NAME', 'Not set')}")
    except:
        print("⚠️  No se pudo obtener configuración de la app")
    
    print("=" * 70)
    print("✅ Servidor iniciado correctamente!")
    print("=" * 70)

def main():
    """Función principal"""
    print("🚀 Iniciando Firefighter BackOffice Production Server...")
    
    # Configuración
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "3001"))
    threads = int(os.getenv("WAITRESS_THREADS", "10"))
    connection_limit = int(os.getenv("WAITRESS_CONNECTION_LIMIT", "1000"))
    channel_timeout = int(os.getenv("WAITRESS_CHANNEL_TIMEOUT", "60"))
    
    # Crear aplicación
    print("🔧 Creando aplicación Flask...")
    app = create_app_with_fallback()
    
    # Inicializar monitores
    print("📊 Inicializando monitores...")
    health_monitor = HealthMonitor(port)
    shutdown_handler = GracefulShutdown()
    
    # Banner informativo
    print_banner(app, host, port, threads)
    
    # Thread para health checks periódicos
    def health_check_worker():
        while not shutdown_handler.should_stop():
            time.sleep(30)
            if health_monitor.check_health():
                status = health_monitor.get_status()
                print(f"✅ Health check passed: {status['status']} | Uptime: {status['uptime']} | Requests: {status['requests']}")
            else:
                status = health_monitor.get_status()
                print(f"⚠️  Health check failed: {status['status']}")
    
    health_thread = Thread(target=health_check_worker, daemon=True)
    health_thread.start()
    
    # Thread para monitorear shutdown
    def shutdown_monitor():
        while not shutdown_handler.should_stop():
            time.sleep(1)
        
        print("\n⚠️  Iniciando shutdown graceful...")
        print("⏳ Esperando que requests en curso terminen...")
        time.sleep(5)  # Dar tiempo para que requests terminen
        print("✅ Shutdown completo")
        sys.exit(shutdown_handler.exit_code)
    
    shutdown_thread = Thread(target=shutdown_monitor, daemon=True)
    shutdown_thread.start()
    
    # Middleware para contar requests
    @app.before_request
    def count_request():
        health_monitor.increment_requests()
    
    # Endpoint de health para el servidor
    @app.route('/server/health')
    def server_health():
        return health_monitor.get_status()
    
    # Endpoint de información del servidor
    @app.route('/server/info')
    def server_info():
        import platform
        import psutil
        
        info = {
            'server': 'waitress',
            'python_version': platform.python_version(),
            'platform': platform.platform(),
            'hostname': socket.gethostname(),
            'cpu_count': psutil.cpu_count() if hasattr(psutil, 'cpu_count') else 'N/A',
            'memory_total': psutil.virtual_memory().total if hasattr(psutil, 'virtual_memory') else 'N/A',
            'memory_available': psutil.virtual_memory().available if hasattr(psutil, 'virtual_memory') else 'N/A',
            'disk_usage': psutil.disk_usage('/').percent if hasattr(psutil, 'disk_usage') else 'N/A',
            'process_id': os.getpid(),
            'uptime': time.time() - health_monitor.start_time,
            'app_mode': 'emergency' if app.config.get('SECRET_KEY') == 'emergency-mode' else 'normal',
            'endpoints': ['/', '/health', '/debug', '/server/health', '/server/info']
        }
        
        return info
    
    try:
        # Iniciar servidor Waitress
        print(f"🌐 Servidor listo en http://{host}:{port}")
        print(f"📞 Health endpoint: http://{host}:{port}/server/health")
        print(f"📋 Info endpoint: http://{host}:{port}/server/info")
        print("⏳ Esperando conexiones...")
        
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=connection_limit,
            channel_timeout=channel_timeout,
            cleanup_interval=30,
            asyncore_use_poll=True,
            url_scheme='https' if app.config.get('SESSION_COOKIE_SECURE', False) else 'http',
            ident="Firefighter BackOffice",
            _quiet=True  # Reducir logs de Waitress
        )
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupción por teclado recibida")
    except Exception as e:
        print(f"💀 ERROR en servidor: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    # Configurar logging básico
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    sys.exit(main())