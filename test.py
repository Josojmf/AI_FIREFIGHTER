import requests

# Probar si los endpoints del dashboard existen
def test_dashboard_endpoints():
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/api/dashboard/stats",
        "/api/dashboard/system-info", 
        "/api/dashboard/health"
    ]
    
    print("🧪 Probando endpoints del dashboard...")
    
    for endpoint in endpoints:
        try:
            url = base_url + endpoint
            print(f"📡 Probando: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint} - EXISTE Y FUNCIONA")
            elif response.status_code == 404:
                print(f"   ❌ {endpoint} - NO EXISTE (404)")
            else:
                print(f"   ⚠️ {endpoint} - Error {response.status_code}")
                
        except Exception as e:
            print(f"   🚫 {endpoint} - Error: {e}")

if __name__ == "__main__":
    test_dashboard_endpoints()