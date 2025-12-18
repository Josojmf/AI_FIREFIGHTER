#!/usr/bin/env python3
"""
Script de diagnóstico para problemas de sesión del BackOffice
"""

import os
import sys
import requests
import json
from datetime import datetime

def check_session_config():
    """Verificar configuración de sesiones"""
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN DE SESIONES")
    print("=" * 60)
    
    # Variables de entorno críticas
    critical_vars = [
        'SECRET_KEY', 'BACKOFFICE_SECRET_KEY', 
        'API_BASE_URL', 'BACKOFFICE_API_BASE_URL',
        'SESSION_COOKIE_NAME', 'ENVIRONMENT'
    ]
    
    print("📋 Variables de entorno:")
    for var in critical_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var or 'KEY' in var:
                print(f"   {var}: {value[:20]}...")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ NO CONFIGURADO")
    
    print("\n")

def test_api_connection():
    """Probar conexión con la API"""
    print("🔌 PRUEBA DE CONEXIÓN API")
    print("=" * 40)
    
    api_urls = [
        'http://localhost:5000',
        'http://backend:5000',
        'http://127.0.0.1:5000'
    ]
    
    for url in api_urls:
        try:
            response = requests.get(f"{url}/health", timeout=5)
            print(f"✅ {url}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {url}: {str(e)}")
    
    print("\n")

def test_login_flow():
    """Probar el flujo de login básico"""
    print("🔐 PRUEBA DE FLUJO DE LOGIN")
    print("=" * 40)
    
    # Datos de prueba
    login_data = {
        'username': 'admin',
        'password': 'admin123'  # Cambiar según tu configuración
    }
    
    api_urls = [
        'http://localhost:5000',
        'http://backend:5000'
    ]
    
    for base_url in api_urls:
        try:
            print(f"📡 Probando login en {base_url}")
            response = requests.post(
                f"{base_url}/api/login",
                json=login_data,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Login exitoso")
                print(f"   Token: {data.get('access_token', '')[:30]}...")
                print(f"   User: {data.get('user', {}).get('username')}")
                
                # Probar validación del token
                if 'access_token' in data:
                    headers = {'Authorization': f"Bearer {data['access_token']}"}
                    try:
                        validate_response = requests.get(
                            f"{base_url}/api/users/me",
                            headers=headers,
                            timeout=5
                        )
                        print(f"   Token válido: {validate_response.status_code == 200}")
                    except Exception as e:
                        print(f"   Error validando token: {e}")
            else:
                print(f"   ❌ Login falló: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("")

def check_docker_services():
    """Verificar estado de servicios Docker"""
    print("🐳 ESTADO DE SERVICIOS DOCKER")
    print("=" * 40)
    
    services = ['backend', 'frontend', 'redis']
    
    for service in services:
        try:
            # Intentar conectar a cada servicio
            urls = {
                'backend': 'http://backend:5000/health',
                'frontend': 'http://frontend:8000/',
                'redis': 'redis://redis:6379'
            }
            
            if service == 'redis':
                # Para Redis, solo reportar que está configurado
                print(f"📦 {service}: Configurado (no se puede probar desde aquí)")
            else:
                try:
                    response = requests.get(urls[service], timeout=3)
                    print(f"✅ {service}: Activo ({response.status_code})")
                except:
                    print(f"❌ {service}: No responde")
                    
        except Exception as e:
            print(f"⚠️ {service}: Error - {e}")
    
    print("\n")

def generate_session_test_config():
    """Generar configuración temporal para testing"""
    print("🛠️ CONFIGURACIÓN TEMPORAL RECOMENDADA")
    print("=" * 50)
    
    config = """
# Configuración temporal para resolver problemas de sesión

# 1. En config.py del BackOffice, cambiar:
SESSION_PROTECTION = 'basic'  # En lugar de 'strong'
SESSION_REFRESH_EACH_REQUEST = False  # En lugar de True
PERMANENT_SESSION_LIFETIME = 3600 * 12  # Aumentar a 12 horas

# 2. Variables de entorno adicionales:
BACKOFFICE_SESSION_DEBUG = true
FLASK_ENV = development
FLASK_DEBUG = true

# 3. Headers de depuración en requests:
headers = {
    'User-Agent': 'FirefighterAI-BackOffice/1.0',
    'X-Requested-With': 'XMLHttpRequest'
}
"""
    
    print(config)

def main():
    """Función principal de diagnóstico"""
    print("🚨 DIAGNÓSTICO DE PROBLEMAS DE SESIÓN - FIREFIGHTER BACKOFFICE")
    print("=" * 70)
    print(f"Fecha: {datetime.now()}")
    print(f"Directorio: {os.getcwd()}")
    print("=" * 70)
    print("\n")
    
    # Ejecutar todas las pruebas
    check_session_config()
    test_api_connection()
    test_login_flow()
    check_docker_services()
    generate_session_test_config()
    
    print("🎯 RECOMENDACIONES:")
    print("=" * 30)
    print("1. Verificar que BACKOFFICE_SECRET_KEY sea diferente a SECRET_KEY")
    print("2. Cambiar SESSION_PROTECTION de 'strong' a 'basic' temporalmente")
    print("3. Verificar que las URLs de API sean correctas")
    print("4. Revisar logs de Docker para errores de conexión")
    print("5. Considerar usar SESSION_REFRESH_EACH_REQUEST = False")
    print("\n")

if __name__ == "__main__":
    main()