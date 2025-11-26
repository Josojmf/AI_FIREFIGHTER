#!/usr/bin/env python3
"""
test_email.py - Script de diagnóstico para email SendGrid
Ejecutar desde el directorio API: python test_email.py
"""

import os
import sys
import traceback
from datetime import datetime, timedelta

# Agregar el directorio actual al path para importar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_email_service():
    """Test completo del servicio de email"""
    print("🚀 DIAGNÓSTICO DE EMAIL SERVICE")
    print("="*60)
    
    # Test 1: Verificar imports
    print("\n1️⃣ VERIFICANDO IMPORTS...")
    try:
        from services.email_service import send_token_email, EmailService
        print("✅ Import exitoso")
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        print("💡 Solución: Verifica que existe el directorio 'services' con email_service.py")
        return False
    except Exception as e:
        print(f"❌ Error inesperado en import: {e}")
        return False
    
    # Test 2: Verificar SendGrid
    print("\n2️⃣ VERIFICANDO SENDGRID...")
    try:
        from sendgrid import SendGridAPIClient
        print("✅ SendGrid importado correctamente")
    except ImportError:
        print("❌ SendGrid no instalado")
        print("💡 Solución: pip install sendgrid==6.9.7")
        return False
    
    # Test 3: Verificar configuración
    print("\n3️⃣ VERIFICANDO CONFIGURACIÓN...")
    service = EmailService()
    
    if not service.api_key or service.api_key == "your-sendgrid-api-key":
        print("❌ API Key no configurada")
        print("💡 Solución: Configura SENDGRID_API_KEY en las variables de entorno")
        return False
    
    print(f"✅ API Key configurada: {service.api_key[:20]}...")
    print(f"✅ Sender email: {service.sender_email}")
    print(f"✅ Sender name: {service.sender_name}")
    
    # Test 4: Test de envío
    print("\n4️⃣ TEST DE ENVÍO DE EMAIL...")
    
    # Solicitar email de prueba
    test_email = input("📧 Introduce un email para el test (o presiona Enter para test@example.com): ").strip()
    if not test_email:
        test_email = "test@example.com"
    
    # Crear datos de prueba
    test_token = "TEST_TOKEN_123456"
    test_name = "Test Token"
    test_max_uses = 5
    test_expires = (datetime.now() + timedelta(days=30)).isoformat()
    
    try:
        print(f"📤 Enviando email de prueba a: {test_email}")
        result = send_token_email(
            recipient_email=test_email,
            token_name=test_name,
            token_value=test_token,
            max_uses=test_max_uses,
            expires_at=test_expires,
            created_by="test_script"
        )
        
        if result:
            print("✅ ✅ ✅ EMAIL ENVIADO CORRECTAMENTE!")
            print("💡 Revisa tu bandeja de entrada y spam")
        else:
            print("❌ Error al enviar email")
            print("💡 Revisa los logs arriba para detalles del error")
            
        return result
        
    except Exception as e:
        print(f"❌ Error en test de envío: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return False

def check_environment():
    """Verificar variables de entorno"""
    print("\n🔧 VARIABLES DE ENTORNO:")
    print("-" * 40)
    
    env_vars = [
        "SENDGRID_API_KEY",
        "SENDGRID_SENDER_EMAIL", 
        "SENDGRID_SENDER_NAME",
        "FRONTEND_URL"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if "API_KEY" in var:
                print(f"✅ {var}: {value[:20]}...")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: No configurado")
    
    print("\n💡 Para configurar variables de entorno:")
    print("   - Windows: set SENDGRID_API_KEY=tu_api_key")
    print("   - Linux/Mac: export SENDGRID_API_KEY=tu_api_key")
    print("   - O agrégalas al archivo .env")

def main():
    print("🔍 DIAGNÓSTICO COMPLETO DE EMAIL")
    print("="*60)
    
    # Verificar variables de entorno
    check_environment()
    
    # Test principal
    success = test_email_service()
    
    print("\n" + "="*60)
    if success:
        print("🎉 DIAGNÓSTICO COMPLETADO - EMAIL FUNCIONA CORRECTAMENTE")
    else:
        print("🚨 DIAGNÓSTICO COMPLETADO - HAY PROBLEMAS CON EMAIL")
        print("\n🛠️  PASOS PARA SOLUCIONARLO:")
        print("1. Verifica que SendGrid esté instalado: pip install sendgrid==6.9.7")
        print("2. Crea el directorio services/ en API/")
        print("3. Copia email_service.py al directorio services/")
        print("4. Verifica tu API key de SendGrid")
        print("5. Configura las variables de entorno")
    print("="*60)

if __name__ == "__main__":
    main()