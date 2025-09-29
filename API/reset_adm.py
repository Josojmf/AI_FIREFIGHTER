import requests
import json

# Configuración
API_URL = "http://localhost:5000/api"

def reset_admin_password():
    try:
        # 1. Login con las credenciales actuales (si las sabes)
        # Si no, vamos directamente al reset
        
        # 2. Solicitar reset de password
        print("Solicitando token de reset...")
        reset_response = requests.post(
            f"{API_URL}/forgot-password",
            json={"email": "admin@firefighter.com"}
        )
        
        print("Respuesta del reset:", reset_response.json())
        
        # El token se imprime en la consola de la API
        print("\n⚠️  Revisa la consola donde corre api.py y busca el token de reset")
        print("💡 Debería verse algo como: [RESET] Token para admin@firefighter.com: http://localhost:8000/reset-password?token=TOKEN_AQUI")
        
        token = input("Pega el token aquí: ").strip()
        
        # 3. Resetear contraseña
        reset_result = requests.post(
            f"{API_URL}/reset-password",
            json={"token": token, "new_password": "admin123"}
        )
        
        print("Resultado del reset:", reset_result.json())
        
        if reset_result.json().get("ok"):
            print("✅ Contraseña cambiada a 'admin123'")
            
            # 4. Probar login
            login_response = requests.post(
                f"{API_URL}/login",
                json={"username": "admin", "password": "admin123"}
            )
            
            print("Prueba de login:", login_response.json())
            
        else:
            print("❌ Error cambiando contraseña")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_admin_password()