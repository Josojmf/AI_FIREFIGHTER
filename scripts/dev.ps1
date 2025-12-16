# scripts/dev.ps1
# Script unificado para desarrollo local con Docker Compose

param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'stop', 'restart', 'rebuild', 'logs', 'status', 'clean')]
    [string]$Action = 'start',
    
    [Parameter(Position=1)]
    [ValidateSet('backend', 'frontend', 'backoffice', 'all')]
    [string]$Service = 'all'
)

$ErrorActionPreference = "Stop"

function Show-Banner {
    Write-Host ""
    Write-Host "🔥 FirefighterAI - Development Environment" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Docker {
    if (-not (docker info 2>$null)) {
        Write-Host "❌ Docker Desktop no está corriendo" -ForegroundColor Red
        Write-Host "💡 Inicia Docker Desktop y vuelve a intentar" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Docker Desktop activo" -ForegroundColor Green
}

function Test-EnvFile {
    if (-not (Test-Path ".env")) {
        Write-Host "❌ Archivo .env no encontrado" -ForegroundColor Red
        Write-Host "💡 Crea el archivo .env primero" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "✅ Archivo .env encontrado" -ForegroundColor Green
}

function Start-DevEnvironment {
    Write-Host "🚀 Iniciando entorno de desarrollo..." -ForegroundColor Cyan
    
    Test-Docker
    Test-EnvFile
    
    Write-Host ""
    Write-Host "🏗️ Construyendo imágenes..." -ForegroundColor Yellow
    docker-compose build
    
    Write-Host ""
    Write-Host "🚀 Iniciando servicios..." -ForegroundColor Yellow
    docker-compose up -d
    
    Write-Host ""
    Write-Host "⏳ Esperando que los servicios inicien (15s)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Show-Status
    
    Write-Host ""
    Write-Host "✅ Entorno iniciado" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Servicios disponibles:" -ForegroundColor Cyan
    Write-Host "   - Frontend:   http://localhost:8000" -ForegroundColor White
    Write-Host "   - Backend:    http://localhost:5000" -ForegroundColor White
    Write-Host "   - BackOffice: http://localhost:3001" -ForegroundColor White
}

function Stop-DevEnvironment {
    Write-Host "🛑 Deteniendo entorno..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Entorno detenido" -ForegroundColor Green
}

function Restart-DevEnvironment {
    Write-Host "🔄 Reiniciando entorno..." -ForegroundColor Yellow
    docker-compose restart
    Start-Sleep -Seconds 10
    Show-Status
    Write-Host "✅ Entorno reiniciado" -ForegroundColor Green
}

function Rebuild-DevEnvironment {
    Write-Host "🏗️ Reconstruyendo entorno completo..." -ForegroundColor Yellow
    
    Write-Host ""
    Write-Host "🛑 Deteniendo servicios..." -ForegroundColor Yellow
    docker-compose down
    
    Write-Host ""
    Write-Host "🧹 Limpiando imágenes viejas..." -ForegroundColor Yellow
    docker-compose build --no-cache
    
    Write-Host ""
    Write-Host "🚀 Iniciando servicios..." -ForegroundColor Yellow
    docker-compose up -d
    
    Start-Sleep -Seconds 15
    Show-Status
    Write-Host "✅ Reconstrucción completada" -ForegroundColor Green
}

function Show-Logs {
    if ($Service -eq 'all') {
        Write-Host "📋 Logs de todos los servicios (Ctrl+C para salir):" -ForegroundColor Cyan
        docker-compose logs -f
    } else {
        Write-Host "📋 Logs de $Service (Ctrl+C para salir):" -ForegroundColor Cyan
        docker-compose logs -f $Service
    }
}

function Show-Status {
    Write-Host "📊 Estado de los contenedores:" -ForegroundColor Cyan
    docker-compose ps
}

function Clean-DevEnvironment {
    Write-Host "🧹 Limpieza completa del entorno..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "⚠️ ADVERTENCIA: Esto eliminará:" -ForegroundColor Red
    Write-Host "   - Todos los contenedores" -ForegroundColor White
    Write-Host "   - Todas las imágenes del proyecto" -ForegroundColor White
    Write-Host "   - Volúmenes no nombrados" -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "¿Continuar? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ Operación cancelada" -ForegroundColor Yellow
        return
    }
    
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    Write-Host "✅ Limpieza completada" -ForegroundColor Green
}

# Main execution
Show-Banner

switch ($Action) {
    'start'   { Start-DevEnvironment }
    'stop'    { Stop-DevEnvironment }
    'restart' { Restart-DevEnvironment }
    'rebuild' { Rebuild-DevEnvironment }
    'logs'    { Show-Logs }
    'status'  { Test-Docker; Show-Status }
    'clean'   { Clean-DevEnvironment }
}

Write-Host ""
