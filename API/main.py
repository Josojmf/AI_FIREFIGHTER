"""
main.py - Punto de entrada para Docker con logs mejorados
=========================================================
"""

import os
import sys
import logging
import uvicorn

# Configurar logging para ver TODO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Añadir directorios al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, "routes"))
sys.path.insert(0, os.path.join(current_dir, "models"))
sys.path.insert(0, os.path.join(current_dir, "utils"))

print("=" * 60)
print("🚀 Firefighter API - STARTING FROM main.py")
print("=" * 60)
print(f"📁 Current directory: {current_dir}")
print(f"📁 Files in directory:")
for f in os.listdir(current_dir):
    if f.endswith('.py'):
        print(f"  • {f}")

# Intentar importar la app
print("\n🔍 Importing api...")
try:
    from api import app
    print("✅ API imported successfully")
    
    # Verificar rutas registradas
    print(f"\n📋 Total routes: {len(app.routes)}")
    if len(app.routes) > 0:
        print("📌 Registered routes (first 20):")
        for route in app.routes[:20]:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'GET'
            print(f"  {methods} {route.path}")
    else:
        print("⚠️  WARNING: No routes registered!")
        
except ImportError as e:
    print(f"❌ FATAL: Cannot import api: {e}")
    print("\n📁 Directory structure:")
    for root, dirs, files in os.walk(current_dir):
        level = root.replace(current_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            if file.endswith('.py'):
                print(f'{subindent}{file}')
    sys.exit(1)
except Exception as e:
    print(f"❌ FATAL: Error during import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("✅ API ready to serve")
print("=" * 60)

if __name__ == "__main__":
    # Obtener configuración de entorno
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5000"))
    
    print(f"🌐 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )