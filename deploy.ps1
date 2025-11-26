# deploy.ps1 - Script de deploy a producción
param([string]$Message = "Automated deployment")

Write-Host "🚀 DESPLEGANDO A PRODUCCIÓN..." -ForegroundColor Green

# Verificar archivos críticos
$files = @("config.py", ".env.production")
foreach ($file in $files) {
    if (!(Test-Path $file)) {
        Write-Host "❌ Error: $file no encontrado" -ForegroundColor Red
        exit 1
    }
}

# Git commit y push
git add .
git commit -m "$Message - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push origin main

Write-Host "✅ Deploy iniciado - GitHub Actions se encargará del resto" -ForegroundColor Green
Write-Host "🌐 URLs de producción:" -ForegroundColor Cyan
Write-Host "   📡 API: http://167.71.63.108:5000" -ForegroundColor White
Write-Host "   🖥️ Frontend: http://167.71.63.108:8000" -ForegroundColor White
Write-Host "   ⚙️ BackOffice: http://167.71.63.108:8080" -ForegroundColor White
