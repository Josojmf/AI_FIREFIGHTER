"""
Run Backoffice in Local Mode (NO DOCKER)
=========================================
"""

import os
import sys

# Forzar modo local (no Docker)
os.environ['DOCKER'] = 'false'
os.environ['API_BASE_URL'] = 'http://localhost:5000'
os.environ['DEBUG'] = 'true'

# Asegurar que estamos en el directorio correcto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar y ejecutar
try:
    from app import app
    print("=" * 70)
    print("🚀 FIREFIGHTER BACKOFFICE - LOCAL MODE")
    print("=" * 70)
    print(f"🌐 Backoffice URL: http://localhost:5001")
    print(f"🔗 API URL: http://localhost:5000")
    print(f"🐛 Debug: True")
    print("=" * 70)
    
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=True,
        threaded=True
    )
except ImportError as e:
    print(f"❌ Error importing app: {e}")
    print("Asegúrate de tener los archivos correctos:")
    print("1. app/__init__.py")
    print("2. config.py")
    print("3. app/models/user.py")
    print("4. app/routes/auth.py")