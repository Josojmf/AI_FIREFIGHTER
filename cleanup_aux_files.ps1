# cleanup_aux_files.ps1 - Limpiar archivos auxiliares del proyecto
Write-Host "🗑️ LIMPIANDO ARCHIVOS AUXILIARES..." -ForegroundColor Yellow

# Archivos relacionados con implementación de cache y verificaciones
$auxFiles = @(
    # Scripts de cache y verificación
    "simple_memory_cache.py",
    "cached_functions.py", 
    "implement_memory_cache.py",
    "implement_memory_cache_fixed.py",
    "apply_cache_to_real_structure.py",
    "fix_api_email_service.py",
    "test_performance_indexes.py",
    "production_cache_config.py",
    "diagnose_cache_error.py",
    "test_cache_simple.py",
    "quick_deploy_check.ps1",
    "check_fixed.ps1",
    "comprehensive_pre_deploy_check.ps1",
    "pre_deploy_check.ps1",
    "run_cache_diagnosis.ps1",
    "implement_cache.ps1",
    "implement_cache_fixed.ps1",
    "apply_cache_real.ps1",
    "quick_performance_wins.ps1",
    
    # Scripts MongoDB
    "create_mongo_indexes.py",
    "verify_mongo_indexes.py", 
    "implement_mongo_indexes.ps1",
    "mongo_indexes.py",
    
    # Archivos temporales y backups
    "temp_*.py",
    "backup_*",
    "backup_before_cache_*",
    "backup_cache_*",
    "*_backup_*",
    
    # Archivos de log y testing
    "pre_deploy_*.log",
    "cache_*.log",
    "deploy_*.log",
    "error_*.log",
    "output_*.log",
    
    # Archivos de configuración temporal
    "temp_cache_test.py",
    "temp_db_test.py",
    "temp_import_test.py",
    "temp_index_test.py",
    "temp_security_test.py",
    
    # Archivos específicos de implementación
    "mongodb_optimization.py", 
    "caching_strategy.py",
    "frontend_optimization.js",
    "api_optimization.py"
)

# Directorios auxiliares
$auxDirectories = @(
    "backup_before_cache_*",
    "backup_cache_*"
)

$deletedFiles = @()
$deletedDirs = @()

Write-Host "`n📁 ARCHIVOS A ELIMINAR:" -ForegroundColor Cyan

foreach ($pattern in $auxFiles) {
    $files = Get-ChildItem -Path . -Name $pattern -Recurse -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        if (Test-Path $file) {
            try {
                Remove-Item $file -Force
                $deletedFiles += $file
                Write-Host "   ✅ Eliminado: $file" -ForegroundColor Green
            } catch {
                Write-Host "   ❌ Error eliminando: $file" -ForegroundColor Red
            }
        }
    }
}

Write-Host "`n📂 DIRECTORIOS A ELIMINAR:" -ForegroundColor Cyan

foreach ($dirPattern in $auxDirectories) {
    $dirs = Get-ChildItem -Path . -Name $dirPattern -Directory -ErrorAction SilentlyContinue
    
    foreach ($dir in $dirs) {
        if (Test-Path $dir) {
            try {
                Remove-Item $dir -Recurse -Force
                $deletedDirs += $dir
                Write-Host "   ✅ Eliminado: $dir" -ForegroundColor Green
            } catch {
                Write-Host "   ❌ Error eliminando: $dir" -ForegroundColor Red
            }
        }
    }
}

# Limpiar archivos específicos en subdirectorios
$services = @("API", "BO", "FO")
Write-Host "`n🔧 LIMPIANDO SUBDIRECTORIOS DE SERVICIOS:" -ForegroundColor Cyan

foreach ($service in $services) {
    if (Test-Path $service) {
        Write-Host "   📁 Limpiando $service..." -ForegroundColor White
        
        $serviceAuxFiles = @(
            "$service/simple_memory_cache.py",
            "$service/cached_functions.py",
            "$service/cache_examples.py", 
            "$service/temp_*.py",
            "$service/*_test.py",
            "$service/error_*.log",
            "$service/output_*.log"
        )
        
        foreach ($pattern in $serviceAuxFiles) {
            $files = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue
            
            foreach ($file in $files) {
                try {
                    Remove-Item $file.FullName -Force
                    $deletedFiles += $file.Name
                    Write-Host "      ✅ Eliminado: $service/$($file.Name)" -ForegroundColor Green
                } catch {
                    Write-Host "      ❌ Error: $service/$($file.Name)" -ForegroundColor Red
                }
            }
        }
    }
}

Write-Host "`n📊 RESUMEN DE LIMPIEZA:" -ForegroundColor Yellow
Write-Host "   🗑️ Archivos eliminados: $($deletedFiles.Count)" -ForegroundColor White
Write-Host "   📂 Directorios eliminados: $($deletedDirs.Count)" -ForegroundColor White

if ($deletedFiles.Count -gt 0) {
    Write-Host "`n📋 ARCHIVOS ELIMINADOS:" -ForegroundColor Gray
    $deletedFiles | Sort-Object | ForEach-Object { Write-Host "      $_" -ForegroundColor Gray }
}

Write-Host "`n✅ LIMPIEZA COMPLETADA" -ForegroundColor Green
Write-Host "💡 Los archivos auxiliares de implementación han sido eliminados" -ForegroundColor Cyan
Write-Host "🎯 El proyecto ahora solo contiene los archivos esenciales" -ForegroundColor Cyan