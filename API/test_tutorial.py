import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

message = Mail(
    from_email="onfiretesting@outlook.es",
    to_emails="joso.jmf@gmail.com", 
    subject="Sending with Twilio SendGrid is Fun",
    html_content="<strong>and easy to do anywhere, even with Python</strong>"
)

try:
    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    response = sg.send(message)
    print("✅ Email enviado!")
    print(f"Status Code: {response.status_code}")
    print(f"Body: {response.body}")
    print(f"Headers: {response.headers}")
except Exception as e:
    print(f"❌ Error: {e}")

