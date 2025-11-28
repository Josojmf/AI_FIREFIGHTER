# check_fixed.ps1 - Verificación pre-deploy CORREGIDA
param(
    [switch]$SkipServices = $false,
    [string]$LogFile = "pre_deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
)

# Función de logging
function Write-Log {
    param($Message, $Level = "INFO", $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    switch($Level) {
        "ERROR" { Write-Host $logEntry -ForegroundColor Red }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "INFO" { Write-Host $logEntry -ForegroundColor $Color }
        default { Write-Host $logEntry -ForegroundColor White }
    }
    
    Add-Content -Path $LogFile -Value $logEntry -ErrorAction SilentlyContinue
}

Write-Log "🚀 VERIFICACIÓN PRE-DEPLOY FIREFIGHTER AI" "INFO" "Green"
Write-Log "="*60 "INFO" "Gray"

$global:errors = @()
$global:warnings = @()
$global:criticalIssues = @()

# =============================================================================
# VERIFICACIONES CRÍTICAS DE ARCHIVOS
# =============================================================================
function Test-CriticalFiles {
    Write-Log "`n📁 1. VERIFICANDO ARCHIVOS CRÍTICOS..." "INFO" "Cyan"
    
    $criticalFiles = @{
        "API/api.py" = "Backend API principal"
        "API/simple_memory_cache.py" = "Sistema de cache API"
        "API/services/email_service.py" = "Servicio de email API"
        "BO/app.py" = "BackOffice principal"
        "BO/simple_memory_cache.py" = "Sistema de cache BO"
        "FO/main.py" = "Frontend principal"
        "FO/simple_memory_cache.py" = "Sistema de cache FO"
        "docker-compose.yml" = "Configuración Docker"
        ".env" = "Variables de entorno"
    }
    
    $missingCritical = @()
    
    foreach ($file in $criticalFiles.GetEnumerator()) {
        if (Test-Path $file.Key) {
            Write-Log "   ✅ $($file.Key) - $($file.Value)" "SUCCESS"
        } else {
            $missingCritical += $file.Key
            Write-Log "   ❌ FALTANTE: $($file.Key) - $($file.Value)" "ERROR"
            $global:errors += "Archivo crítico faltante: $($file.Key)"
        }
    }
    
    Write-Log "   📊 Archivos críticos: $($criticalFiles.Count - $missingCritical.Count)/$($criticalFiles.Count)" "INFO"
}

# =============================================================================
# VERIFICACIÓN SINTAXIS PYTHON
# =============================================================================
function Test-PythonSyntax {
    Write-Log "`n🐍 2. VERIFICANDO SINTAXIS PYTHON..." "INFO" "Cyan"
    
    $pythonFiles = Get-ChildItem -Recurse -Filter "*.py" | Where-Object { 
        $_.FullName -notlike "*__pycache__*" -and 
        $_.FullName -notlike "*\.git*"
    }
    
    $syntaxErrors = @()
    
    foreach ($file in $pythonFiles) {
        try {
            $result = python -m py_compile $file.FullName 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Log "   ✅ $($file.Name)" "SUCCESS"
            } else {
                Write-Log "   ❌ SYNTAX ERROR: $($file.Name)" "ERROR"
                $syntaxErrors += $file.FullName
                $global:errors += "Error de sintaxis en: $($file.Name)"
            }
        } catch {
            $errorMessage = $_.Exception.Message
            Write-Log "   ⚠️ No se pudo verificar: $($file.Name) - $errorMessage" "WARNING"
            $global:warnings += "No se pudo verificar sintaxis: $($file.Name)"
        }
    }
    
    Write-Log "   📊 Archivos Python verificados: $($pythonFiles.Count)" "INFO"
    Write-Log "   📊 Errores de sintaxis: $($syntaxErrors.Count)" "INFO"
}

# =============================================================================
# VERIFICACIÓN IMPORTS PYTHON
# =============================================================================
function Test-PythonImports {
    Write-Log "`n📦 3. VERIFICANDO IMPORTS PYTHON..." "INFO" "Cyan"
    
    $testScript = @"
import sys
import os

try:
    from simple_memory_cache import memory_cache, cache_result
    print("✅ simple_memory_cache: OK")
except Exception as e:
    print(f"❌ simple_memory_cache: {e}")
    sys.exit(1)

try:
    from flask import Flask
    print("✅ Flask: OK")
except Exception as e:
    print(f"❌ Flask: {e}")
    sys.exit(1)

try:
    from pymongo import MongoClient
    print("✅ PyMongo: OK")
except Exception as e:
    print(f"❌ PyMongo: {e}")
    sys.exit(1)

print("🎉 Dependencias críticas OK")
"@
    
    $directories = @("API", "BO", "FO")
    
    foreach ($dir in $directories) {
        if (Test-Path $dir) {
            Write-Log "   🔍 Verificando imports en $dir..." "INFO"
            Set-Location $dir
            
            $testScript | Out-File -FilePath "temp_test.py" -Encoding UTF8
            
            try {
                $result = python temp_test.py 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "      ✅ Imports OK en $dir" "SUCCESS"
                } else {
                    Write-Log "      ❌ Error imports en $dir" "ERROR"
                    $global:errors += "Error de imports en directorio: $dir"
                }
            } catch {
                $errorMessage = $_.Exception.Message
                Write-Log "      ⚠️ No se pudo verificar imports en $dir - $errorMessage" "WARNING"
            } finally {
                Remove-Item "temp_test.py" -ErrorAction SilentlyContinue
            }
            
            Set-Location ..
        }
    }
}

# =============================================================================
# VERIFICACIÓN DATABASE CONNECTION
# =============================================================================
function Test-DatabaseConnection {
    Write-Log "`n🗄️ 4. VERIFICANDO CONEXIÓN DATABASE..." "INFO" "Cyan"
    
    $dbTestScript = @"
import os
from pymongo import MongoClient
from dotenv import load_dotenv

try:
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DB_NAME", "FIREFIGHTER")
    
    if not mongo_uri:
        print("❌ MONGO_URI no configurado")
        exit(1)
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
    client.server_info()
    
    db = client[db_name]
    
    # Test básico write/read
    test_doc = {"test": True}
    result = db.temp_test.insert_one(test_doc)
    found = db.temp_test.find_one({"_id": result.inserted_id})
    
    if found:
        print("✅ Database connection OK")
        db.temp_test.delete_one({"_id": result.inserted_id})
    else:
        print("❌ Database read/write failed")
        exit(1)
    
except Exception as e:
    print(f"❌ Database error: {e}")
    exit(1)
"@
    
    $dbTestScript | Out-File -FilePath "temp_db_test.py" -Encoding UTF8
    
    try {
        $result = python temp_db_test.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Log "   ✅ Database connection OK" "SUCCESS"
        } else {
            Write-Log "   ❌ Database connection FAILED" "ERROR"
            $global:errors += "Error de conexión a base de datos"
        }
    } catch {
        $errorMessage = $_.Exception.Message
        Write-Log "   ❌ Error ejecutando test de database: $errorMessage" "ERROR"
        $global:errors += "No se pudo ejecutar test de database"
    } finally {
        Remove-Item "temp_db_test.py" -ErrorAction SilentlyContinue
    }
}

# =============================================================================
# VERIFICACIÓN SISTEMA CACHÉ
# =============================================================================
function Test-CacheSystem {
    Write-Log "`n🧠 5. VERIFICANDO SISTEMA DE CACHE..." "INFO" "Cyan"
    
    $cacheTestScript = @"
import sys
from simple_memory_cache import memory_cache, cache_result, get_cache_stats

try:
    # Test set/get
    memory_cache.set("test_key", "test_value", 10)
    retrieved = memory_cache.get("test_key")
    
    if retrieved == "test_value":
        print("✅ Cache set/get: OK")
    else:
        print("❌ Cache set/get: FAILED")
        sys.exit(1)
    
    # Test stats
    stats = get_cache_stats()
    if isinstance(stats, dict):
        print("✅ Cache stats: OK")
    else:
        print("❌ Cache stats: FAILED")
        sys.exit(1)
    
    print("🎉 Sistema de cache: OK")
    
except Exception as e:
    print(f"❌ Cache system error: {e}")
    sys.exit(1)
"@
    
    $services = @("API", "BO", "FO")
    $cacheErrors = @()
    
    foreach ($service in $services) {
        if (Test-Path "$service/simple_memory_cache.py") {
            Write-Log "   🔍 Testing cache en $service..." "INFO"
            Set-Location $service
            
            $cacheTestScript | Out-File -FilePath "temp_cache_test.py" -Encoding UTF8
            
            try {
                $result = python temp_cache_test.py 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Log "      ✅ Cache system OK en $service" "SUCCESS"
                } else {
                    Write-Log "      ❌ Cache system FAILED en $service" "ERROR"
                    $cacheErrors += $service
                }
            } catch {
                $errorMessage = $_.Exception.Message
                Write-Log "      ❌ Error testing cache en $service - $errorMessage" "ERROR"
                $cacheErrors += $service
            } finally {
                Remove-Item "temp_cache_test.py" -ErrorAction SilentlyContinue
            }
            
            Set-Location ..
        } else {
            Write-Log "   ⚠️ simple_memory_cache.py no encontrado en $service" "WARNING"
            $global:warnings += "Sistema de cache no encontrado en $service"
        }
    }
    
    if ($cacheErrors.Count -gt 0) {
        $global:errors += "Errores en sistema de cache: $($cacheErrors -join ', ')"
    }
}

# =============================================================================
# VERIFICACIÓN SERVICIOS (OPCIONAL)
# =============================================================================
function Test-ServiceStartup {
    if ($SkipServices) {
        Write-Log "`n⏭️ 6. SALTANDO VERIFICACIÓN DE SERVICIOS" "INFO" "Yellow"
        return
    }
    
    Write-Log "`n🚀 6. VERIFICANDO STARTUP DE SERVICIOS..." "INFO" "Cyan"
    
    $services = @(
        @{Name="API"; Path="API"; File="api.py"; Port=5000}
        @{Name="BackOffice"; Path="BO"; File="app.py"; Port=8080}
        @{Name="Frontend"; Path="FO"; File="main.py"; Port=8000}
    )
    
    foreach ($service in $services) {
        Write-Log "   🔍 Testing $($service.Name)..." "INFO"
        
        if (-not (Test-Path "$($service.Path)/$($service.File)")) {
            Write-Log "      ❌ Archivo principal no encontrado: $($service.File)" "ERROR"
            $global:errors += "$($service.Name) - archivo principal faltante"
            continue
        }
        
        Set-Location $service.Path
        
        try {
            Write-Log "      🚀 Iniciando $($service.Name)..." "INFO"
            $process = Start-Process python -ArgumentList $service.File -PassThru -WindowStyle Hidden
            
            Start-Sleep 10
            
            if ($process.HasExited) {
                Write-Log "      ❌ $($service.Name) terminó inesperadamente" "ERROR"
                $global:errors += "$($service.Name) no inicia correctamente"
            } else {
                Write-Log "      ✅ $($service.Name) proceso corriendo" "SUCCESS"
                
                # Test HTTP
                try {
                    $url = "http://localhost:$($service.Port)/"
                    $response = Invoke-WebRequest -Uri $url -TimeoutSec 5
                    if ($response.StatusCode -eq 200) {
                        Write-Log "      ✅ $($service.Name) responde HTTP OK" "SUCCESS"
                    } else {
                        Write-Log "      ⚠️ $($service.Name) HTTP status: $($response.StatusCode)" "WARNING"
                    }
                } catch {
                    Write-Log "      ❌ $($service.Name) no responde HTTP" "ERROR"
                    $global:errors += "$($service.Name) no responde HTTP"
                }
            }
            
            if (-not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                Write-Log "      🛑 $($service.Name) detenido" "INFO"
            }
            
        } catch {
            $errorMessage = $_.Exception.Message
            Write-Log "      ❌ Error testing $($service.Name): $errorMessage" "ERROR"
            $global:errors += "Error testing $($service.Name)"
        }
        
        Set-Location ..
    }
}

# =============================================================================
# VERIFICACIÓN CONFIGURACIÓN
# =============================================================================
function Test-Configuration {
    Write-Log "`n⚙️ 7. VERIFICANDO CONFIGURACIÓN..." "INFO" "Cyan"
    
    # Verificar .env
    if (Test-Path ".env") {
        $envContent = Get-Content ".env"
        $requiredVars = @("MONGO_URI", "SECRET_KEY", "DB_NAME")
        $missingVars = @()
        
        foreach ($var in $requiredVars) {
            $found = $envContent | Where-Object { $_ -like "$var=*" }
            if (-not $found) {
                $missingVars += $var
            }
        }
        
        if ($missingVars.Count -eq 0) {
            Write-Log "   ✅ Variables de entorno críticas presentes" "SUCCESS"
        } else {
            Write-Log "   ❌ Variables faltantes: $($missingVars -join ', ')" "ERROR"
            $global:errors += "Variables de entorno faltantes"
        }
    } else {
        Write-Log "   ❌ Archivo .env no encontrado" "ERROR"
        $global:criticalIssues += "Archivo .env faltante"
    }
    
    # Verificar docker-compose.yml
    if (Test-Path "docker-compose.yml") {
        Write-Log "   ✅ docker-compose.yml presente" "SUCCESS"
    } else {
        Write-Log "   ⚠️ docker-compose.yml no encontrado" "WARNING"
        $global:warnings += "docker-compose.yml faltante"
    }
}

# =============================================================================
# REPORTE FINAL
# =============================================================================
function Write-FinalReport {
    Write-Log "`n" "INFO"
    Write-Log "🎯 REPORTE FINAL DE VERIFICACIÓN" "INFO" "Green"
    Write-Log "="*50 "INFO" "Gray"
    
    $totalIssues = $global:errors.Count + $global:criticalIssues.Count
    $totalWarnings = $global:warnings.Count
    
    if ($totalIssues -eq 0 -and $totalWarnings -eq 0) {
        Write-Log "🎉 STATUS: PERFECTO - LISTO PARA DEPLOY" "SUCCESS"
        $deployStatus = "SAFE"
    } elseif ($totalIssues -eq 0) {
        Write-Log "✅ STATUS: BUENO - DEPLOY RECOMENDADO" "SUCCESS"
        $deployStatus = "RECOMMENDED"
    } elseif ($global:criticalIssues.Count -eq 0) {
        Write-Log "⚠️ STATUS: PROBLEMAS MENORES - DEPLOY POSIBLE" "WARNING"
        $deployStatus = "CAUTION"
    } else {
        Write-Log "❌ STATUS: PROBLEMAS CRÍTICOS - NO DEPLOYAR" "ERROR"
        $deployStatus = "BLOCKED"
    }
    
    Write-Log "`n📊 RESUMEN:" "INFO" "Cyan"
    Write-Log "   🔴 Errores críticos: $($global:criticalIssues.Count)" $(if($global:criticalIssues.Count -eq 0) {"SUCCESS"} else {"ERROR"})
    Write-Log "   🟡 Errores menores: $($global:errors.Count)" $(if($global:errors.Count -eq 0) {"SUCCESS"} else {"WARNING"})
    Write-Log "   🟠 Advertencias: $($global:warnings.Count)" $(if($global:warnings.Count -eq 0) {"SUCCESS"} else {"INFO"})
    
    if ($global:criticalIssues.Count -gt 0) {
        Write-Log "`n🚨 ERRORES CRÍTICOS:" "ERROR"
        foreach ($issue in $global:criticalIssues) {
            Write-Log "   ❌ $issue" "ERROR"
        }
    }
    
    if ($global:errors.Count -gt 0) {
        Write-Log "`n⚠️ ERRORES MENORES:" "WARNING"
        foreach ($error in $global:errors) {
            Write-Log "   🟡 $error" "WARNING"
        }
    }
    
    if ($global:warnings.Count -gt 0) {
        Write-Log "`n💡 ADVERTENCIAS:" "INFO"
        foreach ($warning in $global:warnings) {
            Write-Log "   🟠 $warning" "INFO"
        }
    }
    
    Write-Log "`n🎯 RECOMENDACIONES:" "INFO" "Yellow"
    
    switch ($deployStatus) {
        "SAFE" {
            Write-Log "   🚀 DEPLOY SEGURO:" "SUCCESS"
            Write-Log "      git add . && git commit -m 'Performance: Cache + indices optimizados' && git push origin main" "INFO"
        }
        "RECOMMENDED" {
            Write-Log "   ✅ DEPLOY RECOMENDADO:" "SUCCESS"
            Write-Log "      1. Revisar advertencias si necesario" "INFO"
            Write-Log "      2. git add . && git commit -m 'Deploy con cache optimizado' && git push origin main" "INFO"
        }
        "CAUTION" {
            Write-Log "   ⚠️ DEPLOY CON PRECAUCIÓN:" "WARNING"
            Write-Log "      1. Corregir errores menores si posible" "WARNING"
            Write-Log "      2. Deploy en horario de baja actividad" "WARNING"
        }
        "BLOCKED" {
            Write-Log "   🛑 NO DEPLOYAR:" "ERROR"
            Write-Log "      1. Corregir TODOS los errores críticos" "ERROR"
            Write-Log "      2. Re-ejecutar este script" "ERROR"
        }
    }
    
    Write-Log "`n⏰ Verificación completada: $(Get-Date)" "INFO" "Gray"
    Write-Log "📋 Log guardado en: $LogFile" "INFO" "Gray"
    
    switch ($deployStatus) {
        "SAFE" { return 0 }
        "RECOMMENDED" { return 1 }
        "CAUTION" { return 2 }
        "BLOCKED" { return 3 }
        default { return 4 }
    }
}

# =============================================================================
# EJECUCIÓN PRINCIPAL
# =============================================================================

try {
    Test-CriticalFiles
    Test-PythonSyntax
    Test-PythonImports
    Test-DatabaseConnection
    Test-CacheSystem
    Test-ServiceStartup
    Test-Configuration
    
    $exitCode = Write-FinalReport
    exit $exitCode
    
} catch {
    $errorMessage = $_.Exception.Message
    Write-Log "❌ ERROR CRÍTICO EN VERIFICACIÓN: $errorMessage" "ERROR"
    exit 99
}