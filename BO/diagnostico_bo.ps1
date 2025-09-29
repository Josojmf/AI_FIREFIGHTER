# diagnostico_bo.ps1
# Ejecutar desde la raíz del proyecto (C:\INFORMATICA\AI_Firefighter\BO)

$ReportFile = Join-Path -Path (Get-Location) -ChildPath "diagnostico_bo_report.txt"
"==== Diagnóstico Firefighter BackOffice ====" | Out-File -FilePath $ReportFile -Encoding utf8
"Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $ReportFile -Encoding utf8 -Append
"" | Out-File -FilePath $ReportFile -Encoding utf8 -Append

function Append {
    param($Title, $Content)
    "----- $Title -----" | Out-File -FilePath $ReportFile -Encoding utf8 -Append
    $Content | Out-File -FilePath $ReportFile -Encoding utf8 -Append
    "" | Out-File -FilePath $ReportFile -Encoding utf8 -Append
}

# 1) Entorno y directorio actual
Append "Directorio actual" (Get-Location).Path
Append "Contenido (nivel 1)" (Get-ChildItem -Force | Select-Object Mode,LastWriteTime,Length,Name | Format-Table -AutoSize | Out-String)

# 2) Estructura árbol (hasta 3 niveles)
Append "Árbol de ficheros (3 niveles)" (Get-ChildItem -Recurse -Force | Select-Object FullName,Mode,Length | Out-String)

# 3) Mostrar ficheros clave
$files = @("run.py","app\__init__.py","app\auth.py","app\config.py")
foreach ($f in $files) {
    if (Test-Path $f) {
        Append "Contenido: $f" (Get-Content $f -Raw)
    } else {
        Append "Faltante" "No existe: $f"
    }
}

# 4) Comprobar __init__.py en app
$initPath = Join-Path (Join-Path (Get-Location) "app") "__init__.py"
if (Test-Path $initPath) {
    Append "__init__.py en app/" "Existe: $initPath"
} else {
    Append "__init__.py en app/" "NO existe: $initPath"
}

# 5) Info Python
Append "Python ejecutable" (& python -c "import sys,os; print(sys.executable); print('venv=' + (os.getenv('VIRTUAL_ENV') or ''))" 2>&1)
Append "python --version" (& python --version 2>&1)

# 6) sys.path con python -c
$pySysPath = 'import sys, json; print(json.dumps(sys.path, indent=2))'
Append "sys.path" (& python -c $pySysPath 2>&1)

# 7) pip list
Append "pip list (top 50)" (& pip list --format=columns 2>&1 | Select-Object -First 200)

# 8) Variables de entorno
$env_vars = @("BACKOFFICE_SECRET_KEY","API_BASE_URL","DEBUG","MONGO_USER","MONGO_PASS","MONGO_CLUSTER","DB_NAME","MONGO_URI","PYTHONPATH","VIRTUAL_ENV")
$env_report = foreach ($v in $env_vars) { "$v = ${env:$v}" }
Append "Variables de entorno relevantes" $env_report

# 9) Intento de importar app.auth
$pyImport = @"
import traceback, importlib
try:
    importlib.invalidate_caches()
    import app.auth as auth_mod
    print("IMPORT_OK")
    print("auth_mod:", auth_mod)
except Exception as e:
    print("IMPORT_ERROR")
    traceback.print_exc()
"@
Append "Resultado intento import app.auth" (& python -c $pyImport 2>&1)

# 10) Permisos
Append "Permisos carpeta actual (Get-Acl)" ((Get-Acl (Get-Location)).Access | Format-Table -AutoSize | Out-String)

Write-Host "Reporte guardado en: $ReportFile"
Write-Host "------------------"
Get-Content $ReportFile -Tail 40
