# scripts/swarm.ps1
# Script unificado para Docker Swarm local

param(
    [Parameter(Position=0)]
    [ValidateSet('init', 'start', 'stop', 'restart', 'logs', 'scale', 'status', 'clean')]
    [string]$Action = 'start',
    
    [Parameter(Position=1)]
    [string]$Service = '',
    
    [Parameter(Position=2)]
    [int]$Replicas = 2
)

$ErrorActionPreference = "Stop"
$STACK_NAME = "firefighter"
$COMPOSE_FILE = "docker-compose.swarm.local.yml"

function Show-Banner {
    Write-Host ""
    Write-Host "🐳 FirefighterAI - Docker Swarm Local" -ForegroundColor Cyan
    Write-Host "======================================" -ForegroundColor Cyan
    Write-Host ""
}

function Test-Docker {
    if (-not (docker info 2>$null)) {
        Write-Host "❌ Docker Desktop no está corriendo" -ForegroundColor Red
        exit 1
    }
}

function Test-Swarm {
    $swarmStatus = docker info --format '{{.Swarm.LocalNodeState}}' 2>$null
    return ($swarmStatus -eq "active")
}

function Initialize-Swarm {
    Write-Host "🔧 Inicializando Docker Swarm..." -ForegroundColor Cyan
    
    Test-Docker
    
    if (Test-Swarm) {
        Write-Host "✅ Swarm ya está activo" -ForegroundColor Green
    } else {
        docker swarm init
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Swarm inicializado" -ForegroundColor Green
        } else {
            Write-Host "❌ Error al inicializar Swarm" -ForegroundColor Red
            exit 1
        }
    }
    
    Write-Host ""
    Write-Host "📊 Nodos Swarm:" -ForegroundColor Cyan
    docker node ls
    
    Write-Host ""
    Write-Host "💡 Siguiente: .\scripts\swarm.ps1 start" -ForegroundColor Yellow
}

function Build-Images {
    Write-Host "🏗️ Construyendo imágenes..." -ForegroundColor Yellow
    
    docker build -t ai-firefighter-backend:local ./API
    docker build -t ai-firefighter-frontend:local ./FO
    docker build -t ai-firefighter-backoffice:local ./BO
    
    Write-Host "✅ Imágenes construidas" -ForegroundColor Green
}

function Start-SwarmStack {
    Write-Host "🚀 Desplegando stack en Swarm..." -ForegroundColor Cyan
    
    if (-not (Test-Swarm)) {
        Write-Host "❌ Swarm no está activo" -ForegroundColor Red
        Write-Host "💡 Ejecuta: .\scripts\swarm.ps1 init" -ForegroundColor Yellow
        exit 1
    }
    
    if (-not (Test-Path $COMPOSE_FILE)) {
        Write-Host "❌ $COMPOSE_FILE no encontrado" -ForegroundColor Red
        exit 1
    }
    
    # Build images
    Build-Images
    
    # Remove old stack
    Write-Host ""
    Write-Host "🧹 Removiendo stack anterior..." -ForegroundColor Yellow
    docker stack rm $STACK_NAME 2>$null
    Start-Sleep -Seconds 10
    
    # Deploy new stack
    Write-Host ""
    Write-Host "🚀 Desplegando stack..." -ForegroundColor Cyan
    docker stack deploy -c $COMPOSE_FILE $STACK_NAME
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error al desplegar" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "⏳ Esperando servicios (30s)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
    
    Show-Status
    
    Write-Host ""
    Write-Host "✅ Stack desplegado" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Servicios:" -ForegroundColor Cyan
    Write-Host "   - Frontend:   http://localhost:8000" -ForegroundColor White
    Write-Host "   - Backend:    http://localhost:5000" -ForegroundColor White
    Write-Host "   - BackOffice: http://localhost:3001" -ForegroundColor White
}

function Stop-SwarmStack {
    Write-Host "🛑 Deteniendo stack..." -ForegroundColor Yellow
    docker stack rm $STACK_NAME
    Start-Sleep -Seconds 10
    Write-Host "✅ Stack detenido" -ForegroundColor Green
}

function Restart-SwarmStack {
    Stop-SwarmStack
    Start-Sleep -Seconds 5
    Start-SwarmStack
}

function Show-Logs {
    if ($Service -eq '') {
        Write-Host "Selecciona un servicio:" -ForegroundColor Yellow
        Write-Host "1) Backend" -ForegroundColor White
        Write-Host "2) Frontend" -ForegroundColor White
        Write-Host "3) Backoffice" -ForegroundColor White
        
        $selection = Read-Host "Opción (1-3)"
        
        switch ($selection) {
            "1" { $Service = "${STACK_NAME}_backend" }
            "2" { $Service = "${STACK_NAME}_frontend" }
            "3" { $Service = "${STACK_NAME}_backoffice" }
            default {
                Write-Host "❌ Opción inválida" -ForegroundColor Red
                exit 1
            }
        }
    } else {
        $Service = "${STACK_NAME}_$Service"
    }
    
    Write-Host "📋 Logs de $Service (Ctrl+C para salir):" -ForegroundColor Cyan
    docker service logs -f $Service
}

function Scale-Service {
    if ($Service -eq '') {
        Write-Host "❌ Especifica un servicio: backend, frontend, o backoffice" -ForegroundColor Red
        Write-Host "Ejemplo: .\scripts\swarm.ps1 scale backend 3" -ForegroundColor Yellow
        exit 1
    }
    
    $fullServiceName = "${STACK_NAME}_$Service"
    
    Write-Host "🔧 Escalando $fullServiceName a $Replicas réplicas..." -ForegroundColor Cyan
    docker service scale "$fullServiceName=$Replicas"
    
    Start-Sleep -Seconds 5
    
    Write-Host ""
    Write-Host "📊 Estado actualizado:" -ForegroundColor Cyan
    docker service ps $fullServiceName
}

function Show-Status {
    Write-Host "📊 Servicios:" -ForegroundColor Cyan
    docker service ls --filter "label=app=firefighter"
    
    Write-Host ""
    Write-Host "📋 Tareas:" -ForegroundColor Cyan
    docker stack ps $STACK_NAME --no-trunc
}

function Clean-Swarm {
    Write-Host "🧹 Limpieza completa de Swarm..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "⚠️ ADVERTENCIA: Eliminará:" -ForegroundColor Red
    Write-Host "   - Stack $STACK_NAME" -ForegroundColor White
    Write-Host "   - Redes overlay" -ForegroundColor White
    Write-Host "   - Imágenes locales" -ForegroundColor White
    Write-Host ""
    
    $confirm = Read-Host "¿Continuar? (y/N)"
    if ($confirm -ne "y" -and $confirm -ne "Y") {
        Write-Host "❌ Cancelado" -ForegroundColor Yellow
        return
    }
    
    docker stack rm $STACK_NAME 2>$null
    Start-Sleep -Seconds 10
    
    docker container prune -f
    docker network prune -f
    docker image prune -f
    
    $leaveSwarm = Read-Host "¿Desactivar Swarm? (y/N)"
    if ($leaveSwarm -eq "y" -or $leaveSwarm -eq "Y") {
        docker swarm leave --force
        Write-Host "✅ Swarm desactivado" -ForegroundColor Green
    }
    
    Write-Host "✅ Limpieza completada" -ForegroundColor Green
}

# Main execution
Show-Banner
Test-Docker

switch ($Action) {
    'init'    { Initialize-Swarm }
    'start'   { Start-SwarmStack }
    'stop'    { Stop-SwarmStack }
    'restart' { Restart-SwarmStack }
    'logs'    { Show-Logs }
    'scale'   { Scale-Service }
    'status'  { Show-Status }
    'clean'   { Clean-Swarm }
}

Write-Host ""
