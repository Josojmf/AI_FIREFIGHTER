# services/email_service.py - IMPLEMENTACIÓN OFICIAL SENDGRID
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
from datetime import datetime

class EmailService:
    def __init__(self):
        """SendGrid - Implementación oficial"""
        # Tu API Key real
        self.api_key = "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"
        self.sender_email = "onfiretesting@outlook.es"
        self.sender_name = "FirefighterAI"
        
    def send_token_email(self, recipient_email, token_name, token_value, max_uses, expires_at=None, created_by="system"):
        """Enviar email usando la librería oficial de SendGrid"""
        print(f"🚀 ENVIANDO EMAIL (SendGrid Oficial) a: {recipient_email}")
        
        try:
            expires_str = self._format_expires_date(expires_at)
            register_url = f"http://localhost:8000/register?token={token_value}"
            
            # Crear el mensaje según la documentación oficial
            message = Mail(
                from_email=From(self.sender_email, self.sender_name),
                to_emails=To(recipient_email),
                subject=Subject(f"🔐 FirefighterAI - Token: {token_name}"),
                html_content=HtmlContent(self._create_email_html(token_name, token_value, max_uses, expires_str, register_url)),
                plain_text_content=PlainTextContent(self._create_email_text(token_name, token_value, max_uses, expires_str, register_url))
            )
            
            # Crear cliente SendGrid
            sg = SendGridAPIClient(self.api_key)
            
            print("📤 Enviando con SendGrid API Client...")
            response = sg.send(message)
            
            if response.status_code == 202:
                print(f"✅ ✅ ✅ EMAIL ENVIADO CORRECTAMENTE a: {recipient_email}")
                print(f"✅ Status Code: {response.status_code}")
                return True
            else:
                print(f"❌ Error SendGrid: {response.status_code}")
                print(f"❌ Headers: {response.headers}")
                print(f"❌ Body: {response.body}")
                self._show_token_console(recipient_email, token_name, token_value, max_uses, expires_at, created_by)
                return False
                
        except Exception as e:
            print(f"❌ Error en SendGrid: {str(e)}")
            self._show_token_console(recipient_email, token_name, token_value, max_uses, expires_at, created_by)
            return False
    
    def _format_expires_date(self, expires_at):
        if not expires_at:
            return "No expira"
        try:
            expires_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            return expires_date.strftime("%d/%m/%Y a las %H:%M")
        except:
            return expires_at
    
    def _create_email_html(self, token_name, token_value, max_uses, expires_str, register_url):
        """Crear contenido HTML del email"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        .header {{ background: #dc3545; color: white; padding: 30px; text-align: center; }}
        .content {{ padding: 30px; }}
        .token-box {{ background: #f8f9fa; border: 2px dashed #dc3545; padding: 20px; margin: 20px 0; text-align: center; font-family: 'Courier New', monospace; font-size: 18px; font-weight: bold; border-radius: 5px; word-break: break-all; }}
        .button {{ background: #dc3545; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold; }}
        .info-box {{ background: #e8f4fd; border-left: 4px solid #2196F3; padding: 15px; margin: 15px 0; border-radius: 0 5px 5px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 28px;">🚒 FirefighterAI</h1>
            <h2 style="margin: 10px 0 0 0; font-size: 20px;">Token de Acceso</h2>
        </div>
        
        <div class="content">
            <p>Hola,</p>
            <p>Se ha generado un token de acceso para tu cuenta en <strong>FirefighterAI</strong>.</p>
            
            <div class="info-box">
                <h3 style="margin-top: 0; color: #1565C0;">📋 Información del Token</h3>
                <p><strong>Nombre:</strong> {token_name}</p>
                <p><strong>Usos máximos:</strong> {max_uses}</p>
                <p><strong>Expira:</strong> {expires_str}</p>
            </div>
            
            <h3>🔑 Tu Token de Acceso:</h3>
            <div class="token-box">
                {token_value}
            </div>
            
            <div style="text-align: center; margin: 25px 0;">
                <a href="{register_url}" class="button">🎯 REGISTRAR MI CUENTA</a>
            </div>
            
            <p><strong>📝 Instrucciones alternativas:</strong></p>
            <ol>
                <li>Visita: <a href="http://localhost:8000/register">http://localhost:8000/register</a></li>
                <li>Pega el token: <code style="background: #f1f1f1; padding: 2px 5px; border-radius: 3px;">{token_value}</code></li>
                <li>Completa tus datos personales</li>
            </ol>
            
            <p><strong>⚠️ Importante:</strong> Este token es personal e intransferible.</p>
            
            <p>Saludos,<br><strong>El equipo de FirefighterAI</strong></p>
        </div>
    </div>
</body>
</html>
"""
    
    def _create_email_text(self, token_name, token_value, max_uses, expires_str, register_url):
        """Crear versión texto plano para clientes de email que no soportan HTML"""
        return f"""
FIREFIGHTERAI - TOKEN DE ACCESO

Se ha generado un token de acceso para tu cuenta.

INFORMACIÓN:
- Token: {token_value}
- Nombre: {token_name}
- Usos máximos: {max_uses}
- Expira: {expires_str}

ENLACE DIRECTO DE REGISTRO:
{register_url}

INSTRUCCIONES:
1. Haz clic en el enlace arriba O
2. Ve a: http://localhost:8000/register
3. Pega este token: {token_value}
4. Completa tus datos personales

⚠️ Este token es personal e intransferible.

Saludos,
El equipo de FirefighterAI
"""
    
    def _show_token_console(self, recipient_email, token_name, token_value, max_uses, expires_at, created_by):
        """Mostrar en consola si falla el envío"""
        expires_str = self._format_expires_date(expires_at)
        register_url = f"http://localhost:8000/register?token={token_value}"
        
        print("\n" + "="*80)
        print("📧 EMAIL NO ENVIADO - USA ESTOS DATOS MANUALMENTE")
        print("="*80)
        print(f"📍 DESTINATARIO: {recipient_email}")
        print(f"🔑 TOKEN: {token_value}")
        print(f"🌐 ENLACE DIRECTO: {register_url}")
        print(f"🏷️  NOMBRE: {token_name}")
        print(f"📊 USOS: {max_uses}")
        print(f"⏰ EXPIRA: {expires_str}")
        print("="*80)
        print("💡 Comparte el enlace o token por WhatsApp/Email manualmente")
        print("="*80)

# Instancia global
email_service = EmailService()

def send_token_email(recipient_email, token_name, token_value, max_uses, expires_at=None, created_by="system"):
    return email_service.send_token_email(
        recipient_email=recipient_email,
        token_name=token_name,
        token_value=token_value,
        max_uses=max_uses,
        expires_at=expires_at,
        created_by=created_by
    )