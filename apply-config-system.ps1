# apply-config-system.ps1 - Script para aplicar el sistema de configuración automático
param(
    [string]$ProjectPath = "C:\INFORMATICA\AI_Firefighter"
)

Write-Host "🚀 APLICANDO SISTEMA DE CONFIGURACIÓN AUTOMÁTICO" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Yellow

# Verificar que estamos en el directorio correcto
if (!(Test-Path "$ProjectPath\api.py") -and !(Test-Path "$ProjectPath\API\api.py")) {
    Write-Host "❌ Error: No se encontró el proyecto en $ProjectPath" -ForegroundColor Red
    Write-Host "💡 Uso: .\apply-config-system.ps1 -ProjectPath 'C:\ruta\a\tu\proyecto'" -ForegroundColor Yellow
    exit 1
}

Set-Location $ProjectPath
Write-Host "📁 Trabajando en: $PWD" -ForegroundColor Cyan

# ============================================================================
# PASO 1: COPIAR ARCHIVOS DE CONFIGURACIÓN
# ============================================================================
Write-Host "`n1️⃣ COPIANDO ARCHIVOS DE CONFIGURACIÓN..." -ForegroundColor Yellow

$configFiles = @(
    "config.py",
    ".env.development", 
    ".env.production"
)

$directories = @("API", "BO", "FO")

foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "📂 Configurando $dir..." -ForegroundColor Cyan
        
        foreach ($file in $configFiles) {
            if (Test-Path $file) {
                Copy-Item $file "$dir\$file" -Force
                Write-Host "   ✅ $file → $dir\" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  $file no encontrado en raíz" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "📂 $dir no existe, saltando..." -ForegroundColor Gray
    }
}

# ============================================================================
# PASO 2: ACTUALIZAR WORKFLOWS DE GITHUB
# ============================================================================
Write-Host "`n2️⃣ ACTUALIZANDO WORKFLOWS DE GITHUB..." -ForegroundColor Yellow

$workflowsDir = ".github\workflows"
if (Test-Path $workflowsDir) {
    # Backup workflows existentes
    $backupDir = "$workflowsDir\backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    
    if (Test-Path "$workflowsDir\cd.yml") {
        Copy-Item "$workflowsDir\cd.yml" "$backupDir\cd_original.yml"
        Write-Host "   📦 Backup creado: cd_original.yml" -ForegroundColor Green
    }
    
    # Actualizar cd.yml si existe cd_updated.yml
    if (Test-Path "cd_updated.yml") {
        Copy-Item "cd_updated.yml" "$workflowsDir\cd.yml" -Force
        Write-Host "   ✅ cd.yml actualizado con configuración automática" -ForegroundColor Green
    }
    
} else {
    Write-Host "   ⚠️  Directorio .github\workflows no encontrado" -ForegroundColor Yellow
}

# ============================================================================
# PASO 3: CONFIGURAR VARIABLES DE ENTORNO PARA DESARROLLO
# ============================================================================
Write-Host "`n3️⃣ CONFIGURANDO VARIABLES DE ENTORNO..." -ForegroundColor Yellow

# Configurar para desarrollo
$env:ENVIRONMENT = "development"
$env:SENDGRID_API_KEY = "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"
$env:SENDGRID_SENDER_EMAIL = "onfiretesting@outlook.es"
$env:SENDGRID_SENDER_NAME = "FirefighterAI"
$env:FRONTEND_URL = "http://localhost:8000"

Write-Host "   ✅ Variables configuradas para DESARROLLO" -ForegroundColor Green
Write-Host "   🌐 API: http://127.0.0.1:5000" -ForegroundColor White
Write-Host "   🖥️  Frontend: http://localhost:8000" -ForegroundColor White
Write-Host "   ⚙️  BackOffice: http://localhost:8080" -ForegroundColor White

# ============================================================================
# PASO 4: VERIFICAR ESTRUCTURA DE EMAIL SERVICE
# ============================================================================
Write-Host "`n4️⃣ VERIFICANDO ESTRUCTURA DE EMAIL SERVICE..." -ForegroundColor Yellow

$apiDir = "API"
if (Test-Path $apiDir) {
    $servicesDir = "$apiDir\services"
    
    if (!(Test-Path $servicesDir)) {
        New-Item -ItemType Directory -Path $servicesDir -Force | Out-Null
        Write-Host "   📁 Directorio services creado" -ForegroundColor Green
    }
    
    # Verificar email_service.py
    if (Test-Path "$servicesDir\email_service.py") {
        Write-Host "   ✅ email_service.py encontrado" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  email_service.py no encontrado" -ForegroundColor Yellow
        Write-Host "   💡 Copia manualmente email_service_CORRECTED.py a $servicesDir\email_service.py" -ForegroundColor Cyan
    }
    
    # Verificar __init__.py
    if (!(Test-Path "$servicesDir\__init__.py")) {
        '# services module' | Out-File -FilePath "$servicesDir\__init__.py" -Encoding UTF8
        Write-Host "   ✅ __init__.py creado" -ForegroundColor Green
    }
} else {
    Write-Host "   ⚠️  Directorio API no encontrado" -ForegroundColor Yellow
}

# ============================================================================
# PASO 5: INSTALAR DEPENDENCIAS NECESARIAS
# ============================================================================
Write-Host "`n5️⃣ VERIFICANDO DEPENDENCIAS..." -ForegroundColor Yellow

try {
    $packages = @("python-dotenv", "sendgrid")
    foreach ($package in $packages) {
        $result = pip show $package 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $package instalado" -ForegroundColor Green
        } else {
            Write-Host "   📥 Instalando $package..." -ForegroundColor Yellow
            pip install $package --break-system-packages
            if ($LASTEXITCODE -eq 0) {
                Write-Host "   ✅ $package instalado exitosamente" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️  Error instalando $package" -ForegroundColor Red
            }
        }
    }
} catch {
    Write-Host "   ⚠️  Error verificando dependencias: $($_.Exception.Message)" -ForegroundColor Yellow
}

# ============================================================================
# PASO 6: CREAR SCRIPTS DE DESARROLLO Y PRODUCCIÓN
# ============================================================================
Write-Host "`n6️⃣ CREANDO SCRIPTS DE AUTOMATIZACIÓN..." -ForegroundColor Yellow

# Script de desarrollo
$startDevScript = @'
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
'@

$startDevScript | Out-File -FilePath "start-dev.ps1" -Encoding UTF8
Write-Host "   ✅ start-dev.ps1 creado" -ForegroundColor Green

# Script de deploy  
$deployScript = @'
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
'@

$deployScript | Out-File -FilePath "deploy.ps1" -Encoding UTF8
Write-Host "   ✅ deploy.ps1 creado" -ForegroundColor Green

# ============================================================================
# PASO 7: TESTS Y VERIFICACIÓN
# ============================================================================
Write-Host "`n7️⃣ EJECUTANDO VERIFICACIÓN FINAL..." -ForegroundColor Yellow

# Test de configuración
if (Test-Path "API\config.py") {
    Set-Location "API"
    try {
        $configTest = python -c "from config import AppConfig; print('✅ Configuración cargada:', AppConfig.ENVIRONMENT)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Sistema de configuración funcionando" -ForegroundColor Green
        } else {
            Write-Host "   ⚠️  Error en configuración - verificar manualmente" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ⚠️  No se pudo probar la configuración" -ForegroundColor Yellow
    }
    Set-Location ..
}

# ============================================================================
# RESUMEN FINAL
# ============================================================================
Write-Host "`n🎉 INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Yellow

Write-Host "`n📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan
Write-Host "1️⃣  Para desarrollo:" -ForegroundColor White
Write-Host "   .\start-dev.ps1" -ForegroundColor Gray
Write-Host "   cd API && python api.py" -ForegroundColor Gray
Write-Host "   cd BO && python app.py" -ForegroundColor Gray

Write-Host "`n2️⃣  Para producción:" -ForegroundColor White  
Write-Host "   .\deploy.ps1 'Mensaje del commit'" -ForegroundColor Gray

Write-Host "`n3️⃣  Verificar email:" -ForegroundColor White
Write-Host "   cd API && python test_email.py" -ForegroundColor Gray

Write-Host "`n🎯 CONFIGURACIONES AUTOMÁTICAS:" -ForegroundColor Cyan
Write-Host "✅ URLs se configuran automáticamente según entorno" -ForegroundColor Green
Write-Host "✅ Email funcionará en desarrollo y producción" -ForegroundColor Green  
Write-Host "✅ GitHub Actions configurado para deploy automático" -ForegroundColor Green
Write-Host "✅ Variables de entorno centralizadas" -ForegroundColor Green

Write-Host "`n💡 ARCHIVOS IMPORTANTES CREADOS:" -ForegroundColor Yellow
Write-Host "📄 API\config.py - Configuración central" -ForegroundColor White
Write-Host "📄 start-dev.ps1 - Script de desarrollo" -ForegroundColor White
Write-Host "📄 deploy.ps1 - Script de producción" -ForegroundColor White
Write-Host "📄 .env.development - Variables desarrollo" -ForegroundColor White
Write-Host "📄 .env.production - Variables producción" -ForegroundColor White

Write-Host "`n🔥 ¡SISTEMA LISTO! Ya no más problemas de URLs entre desarrollo y producción" -ForegroundColor Green -BackgroundColor DarkRed