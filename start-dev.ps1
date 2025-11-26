# start-dev.ps1 - Script para desarrollo
$env:ENVIRONMENT = "development"
$env:SENDGRID_API_KEY = "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"
$env:SENDGRID_SENDER_EMAIL = "onfiretesting@outlook.es"
$env:SENDGRID_SENDER_NAME = "FirefighterAI"
$env:FRONTEND_URL = "http://localhost:8000"

Write-Host "🏠 CONFIGURACIÓN DE DESARROLLO APLICADA" -ForegroundColor Green
Write-Host "📡 API: http://127.0.0.1:5000" -ForegroundColor White
Write-Host "🖥️ Frontend: http://localhost:8000" -ForegroundColor White
Write-Host "⚙️ BackOffice: http://localhost:8080" -ForegroundColor White
Write-Host "📧 Email configurado automáticamente" -ForegroundColor White
