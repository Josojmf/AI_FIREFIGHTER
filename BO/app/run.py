rom app import create_app
from config import Config

app = create_app()

if __name__ == '__main__':
    print("🚀 Firefighter Backoffice iniciando...")
    print(f"🌐 Panel de administración: http://localhost:8080")
    print(f"🔗 Conectado a API: {Config.API_BASE_URL}")
    
    app.run(host='0.0.0.0', port=8080, debug=Config.DEBUG)