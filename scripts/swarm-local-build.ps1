# scripts/swarm-local-build.ps1
# Construir imágenes locales para Swarm

Write-Host "🏗️ Construyendo imágenes locales para Swarm..." -ForegroundColor Cyan
Write-Host ""

# Verificar que Swarm está activo
$swarmStatus = docker info --format '{{.Swarm.LocalNodeState}}' 2>$null
if ($swarmStatus -ne "active") {
    Write-Host "❌ Swarm no está activo" -ForegroundColor Red
    Write-Host "💡 Ejecuta primero: .\scripts\swarm-local-init.ps1" -ForegroundColor Yellow
    exit 1
}

# Build Backend
Write-Host "🔨 Construyendo Backend..." -ForegroundColor Yellow
docker build -t ai-firefighter-backend:local ./API
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error construyendo Backend" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Backend construido" -ForegroundColor Green

# Build Frontend
Write-Host ""
Write-Host "🔨 Construyendo Frontend..." -ForegroundColor Yellow
docker build -t ai-firefighter-frontend:local ./FO
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error construyendo Frontend" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Frontend construido" -ForegroundColor Green

# Build Backoffice
Write-Host ""
Write-Host "🔨 Construyendo Backoffice..." -ForegroundColor Yellow
docker build -t ai-firefighter-backoffice:local ./BO
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error construyendo Backoffice" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Backoffice construido" -ForegroundColor Green

# Verificar imágenes
Write-Host ""
Write-Host "📦 Imágenes construidas:" -ForegroundColor Cyan
docker images | Select-String "ai-firefighter.*local"

Write-Host ""
Write-Host "✅ Todas las imágenes construidas exitosamente" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Siguiente paso:" -ForegroundColor Yellow
Write-Host "   .\scripts\swarm-local-start.ps1" -ForegroundColor White
