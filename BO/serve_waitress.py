from waitress import serve
from app import create_app

# Crear la aplicación Flask mediante factory
app = create_app() 

if __name__ == "__main__":
    print("🚀 Firefighter Backoffice (Waitress) iniciando...")
    print("🌐 Panel de administración en: http://localhost:3001")
    
    # Ejecutar con waitress
    serve(app, host="0.0.0.0", port=3001, threads=6)
