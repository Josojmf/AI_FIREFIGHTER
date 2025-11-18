from waitress import serve
from app import create_app

app = create_app()

if __name__ == "__main__":
    print("🚀 Firefighter Backoffice (Waitress) iniciando...")
    print("🌐 Panel de administración: http://localhost:3001")

    serve(app, host="0.0.0.0", port=3001, threads=4)
