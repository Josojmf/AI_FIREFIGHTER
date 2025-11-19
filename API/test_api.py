import requests
import json

def test_api_login():
    """Test para ver qué ID devuelve realmente la API"""
    
    print("🔍 Probando login con admin...")
    
    try:
        response = requests.post(
            "http://localhost:5000/api/login",
            json={"username": "admin", "password": "admin123"},
            timeout=10
        )
        
        print(f"📡 Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("📋 Respuesta completa:")
            print(json.dumps(data, indent=2))
            
            if data.get('ok'):
                user_data = data.get('user', {})
                token = data.get('access_token')
                
                print(f"\n✅ Login exitoso!")
                print(f"👤 Username: {user_data.get('username')}")
                print(f"🆔 User ID: {user_data.get('id')}")
                print(f"📧 Email: {user_data.get('email')}")
                print(f"🔑 Role: {user_data.get('role')}")
                print(f"🎫 Token: {token[:20]}..." if token else "Sin token")
                
                # Ahora probemos obtener el usuario por ID
                print(f"\n🔍 Probando GET /api/users/{user_data.get('id')} con token...")
                
                headers = {'Authorization': f'Bearer {token}'}
                get_response = requests.get(
                    f"http://localhost:5000/api/users/{user_data.get('id')}",
                    headers=headers,
                    timeout=10
                )
                
                print(f"📡 GET Status: {get_response.status_code}")
                if get_response.status_code == 200:
                    get_data = get_response.json()
                    print("✅ Usuario obtenido correctamente!")
                    print(json.dumps(get_data, indent=2))
                else:
                    print(f"❌ Error obteniendo usuario: {get_response.text}")
                    
        else:
            print(f"❌ Error en login: {response.text}")
            
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    test_api_login()