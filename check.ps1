# pre_deploy_check.ps1 - Verificación antes de push a producción
Write-Host "🔍 VERIFICACIÓN PRE-DEPLOY A PRODUCCIÓN" -ForegroundColor Yellow
Write-Host "="*60 -ForegroundColor Gray

$errors = @()
$warnings = @()

Write-Host "`n1️⃣ VERIFICANDO API..." -ForegroundColor Cyan

# Verificar que API arranca correctamente
Set-Location API
try {
    Write-Host "   🧪 Testing API startup..." -ForegroundColor White
    $apiTest = Start-Process python -ArgumentList "api.py" -PassThru -WindowStyle Hidden
    Start-Sleep 10
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ API arranca correctamente" -ForegroundColor Green
        } else {
            $errors += "API responde pero con errores"
        }
    } catch {
        $errors += "API no responde - probablemente error de startup"
    }
    
    Stop-Process -Id $apiTest.Id -Force -ErrorAction SilentlyContinue
} catch {
    $errors += "Error ejecutando API: $_"
}
Set-Location ..

Write-Host "`n2️⃣ VERIFICANDO BACKOFFICE..." -ForegroundColor Cyan
Set-Location BO
try {
    Write-Host "   🧪 Testing BackOffice startup..." -ForegroundColor White
    $boTest = Start-Process python -ArgumentList "app.py" -PassThru -WindowStyle Hidden
    Start-Sleep 10
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8080" -TimeoutSec 5
        if ($response.StatusCode -eq 200) {
            Write-Host "   ✅ BackOffice arranca correctamente" -ForegroundColor Green
        } else {
            $warnings += "BackOffice responde pero puede tener problemas"
        }
    } catch {
        $errors += "BackOffice no responde"
    }
    
    Stop-Process -Id $boTest.Id -Force -ErrorAction SilentlyContinue
} catch {
    $errors += "Error ejecutando BackOffice: $_"
}
Set-Location ..

Write-Host "`n3️⃣ VERIFICANDO FRONTEND..." -ForegroundColor Cyan
Set-Location FO
try {
    Write-Host "   🧪 Testing Frontend startup..." -ForegroundColor White
    if (Test-Path "main.py") {
        Write-Host "   ✅ Frontend main.py existe" -ForegroundColor Green
    } else {
        $warnings += "Frontend main.py no encontrado"
    }
} catch {
    $warnings += "Error verificando Frontend"
}
Set-Location ..

Write-Host "`n4️⃣ VERIFICANDO ARCHIVOS CRÍTICOS..." -ForegroundColor Cyan

# Verificar archivos críticos
$criticalFiles = @(
    "API/api.py",
    "API/services/email_service.py",
    "API/simple_memory_cache.py",
    "BO/app.py",
    "BO/simple_memory_cache.py",
    "FO/main.py",
    "FO/simple_memory_cache.py",
    "docker-compose.yml",
    ".env"
)

foreach ($file in $criticalFiles) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        $errors += "Archivo crítico faltante: $file"
        Write-Host "   ❌ $file FALTANTE" -ForegroundColor Red
    }
}

Write-Host "`n5️⃣ VERIFICANDO CONFIGURACIÓN DOCKER..." -ForegroundColor Cyan
if (Test-Path "docker-compose.yml") {
    Write-Host "   ✅ docker-compose.yml existe" -ForegroundColor Green
} else {
    $warnings += "docker-compose.yml no encontrado"
}

Write-Host "`n📊 RESUMEN DE VERIFICACIÓN:" -ForegroundColor Yellow
Write-Host "="*40 -ForegroundColor Gray

if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "🎉 TODO LISTO PARA DEPLOY" -ForegroundColor Green
    Write-Host "✅ Sin errores críticos" -ForegroundColor Green
    Write-Host "✅ Todos los componentes verificados" -ForegroundColor Green
    Write-Host "`n🚀 PUEDES HACER PUSH SEGURO A PRODUCCIÓN" -ForegroundColor Green
    exit 0
    
} elseif ($errors.Count -eq 0) {
    Write-Host "⚠️ DEPLOY POSIBLE CON ADVERTENCIAS" -ForegroundColor Yellow
    Write-Host "✅ Sin errores críticos" -ForegroundColor Green
    Write-Host "⚠️ Advertencias encontradas:" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
    Write-Host "`n🤔 RECOMENDACIÓN: Revisar advertencias antes de deploy" -ForegroundColor Yellow
    exit 1
    
} else {
    Write-Host "❌ DEPLOY NO RECOMENDADO" -ForegroundColor Red
    Write-Host "❌ Errores críticos encontrados:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "   • $err" -ForegroundColor Red
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "`n⚠️ Advertencias adicionales:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "   • $warning" -ForegroundColor Yellow
        }
    }
    
    Write-Host "`n🛑 CORRIGE ERRORES ANTES DE DEPLOY" -ForegroundColor Red
    exit 2
}