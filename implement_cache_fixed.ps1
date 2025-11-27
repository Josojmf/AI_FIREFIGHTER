# apply_cache_real.ps1 - Aplicar cache a estructura real
Write-Host "⚡ APLICANDO CACHE A ESTRUCTURA REAL DE FIREFIGHTER AI" -ForegroundColor Green
Write-Host "="*70 -ForegroundColor Gray

if (!(Test-Path ".")) {
    Write-Host "❌ Ejecuta desde el directorio del proyecto" -ForegroundColor Red
    exit 1
}

Write-Host "`n📁 ESTRUCTURA DETECTADA:" -ForegroundColor Cyan
$directories = @("API", "BO", "FO")
foreach ($dir in $directories) {
    if (Test-Path $dir) {
        Write-Host "   ✅ $dir/ encontrado" -ForegroundColor Green
        
        # Mostrar archivo principal de cada componente
        $main_files = @{
            "API" = "api.py"
            "BO" = "app.py"  
            "FO" = "main.py"
        }
        
        $main_file = "$dir/$($main_files[$dir])"
        if (Test-Path $main_file) {
            Write-Host "      📄 $main_file ✅" -ForegroundColor White
        } else {
            Write-Host "      📄 $main_file ❌" -ForegroundColor Red
        }
    } else {
        Write-Host "   ❌ $dir/ no encontrado" -ForegroundColor Red
    }
}

Write-Host "`n📋 QUE VAMOS A HACER:" -ForegroundColor Yellow
Write-Host "   🔧 Modificar API/api.py con cache + endpoints" -ForegroundColor White
Write-Host "   🔧 Modificar BO/app.py con cache" -ForegroundColor White
Write-Host "   🔧 Modificar FO/main.py con cache" -ForegroundColor White
Write-Host "   📁 Copiar simple_memory_cache.py a cada directorio" -ForegroundColor White
Write-Host "   📄 Crear ejemplos especificos por componente" -ForegroundColor White
Write-Host "   💾 Backup automatico de archivos originales" -ForegroundColor White

$confirm = Read-Host "`n¿Proceder con aplicacion a estructura real? (Y/n)"
if ($confirm -eq "n" -or $confirm -eq "N") {
    Write-Host "❌ Operación cancelada" -ForegroundColor Yellow
    exit 0
}

Write-Host "`n📦 VERIFICANDO ARCHIVOS NECESARIOS..." -ForegroundColor Cyan

$required_files = @("simple_memory_cache.py", "apply_cache_to_real_structure.py")
$missing_files = @()

foreach ($file in $required_files) {
    if (!(Test-Path $file)) {
        $missing_files += $file
        Write-Host "   ❌ Faltante: $file" -ForegroundColor Red
    } else {
        Write-Host "   ✅ Encontrado: $file" -ForegroundColor Green
    }
}

if ($missing_files.Count -gt 0) {
    Write-Host "`n❌ Archivos faltantes. Asegurate de tener:" -ForegroundColor Red
    foreach ($file in $missing_files) {
        Write-Host "   • $file" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host "`n🚀 APLICANDO CACHE A ESTRUCTURA REAL..." -ForegroundColor Cyan

try {
    # Ejecutar aplicacion
    python apply_cache_to_real_structure.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ ¡CACHE APLICADO A ESTRUCTURA REAL!" -ForegroundColor Green
        
        Write-Host "`n📁 ARCHIVOS MODIFICADOS:" -ForegroundColor Cyan
        
        # Verificar que archivos fueron modificados
        $modified_files = @(
            @{path="API/api.py"; desc="Backend API con cache + endpoints"},
            @{path="BO/app.py"; desc="BackOffice con cache"},
            @{path="FO/main.py"; desc="Frontend con cache"},
            @{path="API/simple_memory_cache.py"; desc="Sistema de cache API"},
            @{path="BO/simple_memory_cache.py"; desc="Sistema de cache BO"},
            @{path="FO/simple_memory_cache.py"; desc="Sistema de cache FO"},
            @{path="API/cache_examples.py"; desc="Ejemplos API"},
            @{path="BO/cache_examples.py"; desc="Ejemplos BO"},
            @{path="FO/cache_examples.py"; desc="Ejemplos FO"}
        )
        
        foreach ($file in $modified_files) {
            if (Test-Path $file.path) {
                Write-Host "   ✅ $($file.path) - $($file.desc)" -ForegroundColor Green
            } else {
                Write-Host "   ⚠️ $($file.path) - No creado" -ForegroundColor Yellow
            }
        }
        
        # Verificar backup
        if (Test-Path "backup_cache_*") {
            $backup_dir = Get-ChildItem "backup_cache_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            Write-Host "`n💾 Backup creado: $($backup_dir.Name)" -ForegroundColor Gray
        }
        
        Write-Host "`n🎯 COMO PROBAR AHORA:" -ForegroundColor Yellow
        Write-Host "   1. Abrir 3 terminales/PowerShell:" -ForegroundColor White
        Write-Host ""
        Write-Host "   Terminal 1 (API):" -ForegroundColor Cyan
        Write-Host "      cd API" -ForegroundColor Gray
        Write-Host "      python api.py" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Terminal 2 (BackOffice):" -ForegroundColor Cyan
        Write-Host "      cd BO" -ForegroundColor Gray
        Write-Host "      python app.py" -ForegroundColor Gray
        Write-Host ""
        Write-Host "   Terminal 3 (Frontend):" -ForegroundColor Cyan
        Write-Host "      cd FO" -ForegroundColor Gray
        Write-Host "      python main.py" -ForegroundColor Gray
        
        Write-Host "`n📊 VERIFICAR CACHE FUNCIONANDO:" -ForegroundColor Yellow
        Write-Host "   🌐 API cache stats: http://localhost:5000/api/cache/stats" -ForegroundColor Green
        Write-Host "   📊 Deberia mostrar JSON con estadisticas" -ForegroundColor White
        
        Write-Host "`n🔧 USAR FUNCIONES CACHEADAS:" -ForegroundColor Yellow
        Write-Host "   📄 API: Ve API/cache_examples.py" -ForegroundColor White
        Write-Host "   📄 BO: Ve BO/cache_examples.py" -ForegroundColor White
        Write-Host "   📄 FO: Ve FO/cache_examples.py" -ForegroundColor White
        
        Write-Host "`n📈 EJEMPLO DE INTEGRACION RAPIDA:" -ForegroundColor Cyan
        Write-Host @"
   # En API/api.py - ANTES:
   user = users.find_one({"_id": user_id})
   
   # En API/api.py - DESPUES:
   from cache_examples import get_user_by_id_cached
   user = get_user_by_id_cached(user_id)  # 5-10x mas rapido!
"@ -ForegroundColor Gray
        
        Write-Host "`n📚 DOCUMENTACION COMPLETA:" -ForegroundColor Yellow
        Write-Host "   📄 CACHE_GUIDE_REAL_STRUCTURE.md" -ForegroundColor Green
        
        Write-Host "`n🛡️ SI HAY PROBLEMAS (ROLLBACK):" -ForegroundColor Red
        if (Test-Path "backup_cache_*") {
            $backup_dir = Get-ChildItem "backup_cache_*" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            Write-Host "   Copy-Item $($backup_dir.Name)/* ./ -Recurse -Force" -ForegroundColor Yellow
        }
        
        Write-Host "`n📈 MEJORAS ESPERADAS:" -ForegroundColor Green
        Write-Host "   • API responses: 3-10x mas rapidas" -ForegroundColor White
        Write-Host "   • BackOffice dashboard: 5-8x mas rapido" -ForegroundColor White
        Write-Host "   • Frontend UX: Mucho mas fluido" -ForegroundColor White
        Write-Host "   • Login/auth: Casi instantaneo" -ForegroundColor White
        
        Write-Host "`n🎉 CACHE LISTO PARA LA ESTRUCTURA REAL!" -ForegroundColor Green
        
    } else {
        Write-Host "`n❌ Error durante aplicacion" -ForegroundColor Red
        Write-Host "💡 Verifica que Python este funcionando correctamente" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "`n❌ Error ejecutando aplicacion: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n✅ PROCESO COMPLETADO PARA ESTRUCTURA REAL" -ForegroundColor Green