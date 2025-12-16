# 🚀 FirefighterAI - Infrastructure Setup Script (Sintaxis Corregida)
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("dev", "prod", "monitoring")]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [switch]$CleanUp = $false
)

Write-Host "🔥 FirefighterAI Infrastructure Setup" -ForegroundColor Red
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "=" * 50

# 🔧 Crear archivo .env si no existe
function Create-EnvFile {
    if (!(Test-Path ".env")) {
        Write-Host "📝 Creando archivo .env para desarrollo..." -ForegroundColor Green
        
        $envContent = @"
# FirefighterAI - Development Environment
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key
DB_USERNAME=joso
DB_PASSWORD=XyGItdDKpWkfJfjT
DB_CLUSTER=cluster0.yzzh9ig.mongodb.net
MONGO_URI=mongodb+srv://joso:XyGItdDKpWkfJfjT@cluster0.yzzh9ig.mongodb.net/FIREFIGHTER?retryWrites=true&w=majority
API_BASE_URL=http://localhost:5000
REDIS_URL=redis://redis:6379/0
NODE_ENV=development
ENVIRONMENT=development
DOCKER_ENV=true
DEBUG=true
PORT=8000
"@
        Set-Content -Path ".env" -Value $envContent
        Write-Host "  ✅ Archivo .env creado" -ForegroundColor Green
    } else {
        Write-Host "  ⚡ Archivo .env ya existe" -ForegroundColor Yellow
    }
}

# 📁 Crear estructura
function Create-Infrastructure {
    Write-Host "📁 Verificando estructura de infraestructura..." -ForegroundColor Green
    
    $dirs = @(
        "infra",
        "infra/nginx",
        "infra/nginx/sites-enabled",
        "infra/redis",
        "infra/prometheus"
    )
    
    foreach ($dir in $dirs) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "  ✅ Creado: $dir"
        } else {
            Write-Host "  ⚡ Existe: $dir" -ForegroundColor Yellow
        }
    }
}

# 🐳 Verificar Docker
function Test-Docker {
    Write-Host "🐳 Verificando Docker..." -ForegroundColor Green
    
    try {
        $dockerVersion = docker --version 2>$null
        Write-Host "  ✅ Docker: $dockerVersion" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ❌ Docker no disponible" -ForegroundColor Red
        return $false
    }
}

# 🚀 Desplegar servicios
function Deploy-Services {
    param([string]$env)
    
    Write-Host "🚀 Desplegando servicios para $env..." -ForegroundColor Green
    
    try {
        if ($env -eq "dev") {
            if (Test-Path "docker-compose.dev.yml") {
                Write-Host "  📦 Usando docker-compose.dev.yml" -ForegroundColor Cyan
                docker-compose -f docker-compose.dev.yml up -d
            } else {
                Write-Host "  ❌ docker-compose.dev.yml no encontrado" -ForegroundColor Red
                return $false
            }
        } elseif ($env -eq "prod") {
            Write-Host "  📦 Usando docker-compose.yml (producción)" -ForegroundColor Cyan
            docker-compose up -d
        } elseif ($env -eq "monitoring") {
            Write-Host "  📦 Desplegando con monitoring" -ForegroundColor Cyan
            docker-compose -f docker-compose.dev.yml -f docker-compose.monitoring.yml up -d
        }
        
        Write-Host "  ✅ Comando ejecutado" -ForegroundColor Green
        Write-Host "  ⏳ Esperando 15 segundos..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
        
        # Verificar estado
        Write-Host "  📊 Estado de servicios:" -ForegroundColor Cyan
        docker-compose ps
        
        return $true
        
    } catch {
        Write-Host "  ❌ Error: $_" -ForegroundColor Red
        return $false
    }
}

# 🧹 Limpiar servicios
function Clean-Services {
    Write-Host "🧹 Limpiando servicios..." -ForegroundColor Yellow
    
    try {
        # Parar servicios de desarrollo
        if (Test-Path "docker-compose.dev.yml") {
            docker-compose -f docker-compose.dev.yml down -v 2>$null
        }
        
        # Parar servicios de monitoring  
        if (Test-Path "docker-compose.monitoring.yml") {
            docker-compose -f docker-compose.monitoring.yml down -v 2>$null
        }
        
        Write-Host "  ✅ Limpieza completada" -ForegroundColor Green
        
    } catch {
        Write-Host "  ⚠️ Error durante limpieza: $_" -ForegroundColor Yellow
    }
}

# 📊 Mostrar información
function Show-AccessInfo {
    param([string]$env)
    
    Write-Host ""
    Write-Host "🎯 Configuración completada!" -ForegroundColor Green
    Write-Host "=" * 40
    
    if ($env -eq "dev") {
        Write-Host "📝 Para acceso completo, configura hosts manualmente:" -ForegroundColor Cyan
        Write-Host "   Edita C:\Windows\System32\drivers\etc\hosts como Admin:" -ForegroundColor Yellow
        Write-Host "   127.0.0.1   firefighter.local" -ForegroundColor White
        Write-Host "   127.0.0.1   api.firefighter.local" -ForegroundColor White
        Write-Host "   127.0.0.1   admin.firefighter.local" -ForegroundColor White
        
        Write-Host ""
        Write-Host "🌐 URLs disponibles:" -ForegroundColor Green
        Write-Host "   Frontend:   http://localhost:8000 (directo)" -ForegroundColor Cyan
        Write-Host "   API:        http://localhost:5000 (directo)" -ForegroundColor Cyan
        Write-Host "   BackOffice: http://localhost:3001 (directo)" -ForegroundColor Cyan
        Write-Host "   Redis:      localhost:6379" -ForegroundColor Magenta
        
        Write-Host ""
        Write-Host "📋 Comandos útiles:" -ForegroundColor Green
        Write-Host "   docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor White
        Write-Host "   docker-compose -f docker-compose.dev.yml ps" -ForegroundColor White
        Write-Host "   docker-compose -f docker-compose.dev.yml down" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "🎯 ¡Infraestructura lista!" -ForegroundColor Yellow
}

# 🚀 Función principal
function Main {
    if ($CleanUp) {
        Clean-Services
        return
    }
    
    if (!(Test-Docker)) {
        return
    }
    
    Create-Infrastructure
    Create-EnvFile
    
    if (Deploy-Services -env $Environment) {
        Show-AccessInfo -env $Environment
    } else {
        Write-Host ""
        Write-Host "❌ Error en deployment" -ForegroundColor Red
    }
}

# Ejecutar
try {
    Main
} catch {
    Write-Host ""
    Write-Host "❌ Error: $_" -ForegroundColor Red
}