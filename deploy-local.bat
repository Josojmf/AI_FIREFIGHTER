@echo off
REM deploy-local.bat - Script para desarrollo local en Windows

echo ===================================
echo  INICIANDO ENTORNO DE DESARROLLO
echo ===================================

REM Verificar que Docker está corriendo
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker no está corriendo
    echo Por favor inicia Docker Desktop
    pause
    exit /b 1
)

REM Cargar variables de entorno de desarrollo
if exist .env.development (
    echo ✓ Cargando variables de desarrollo...
    for /f "tokens=*" %%i in (.env.development) do set %%i
) else (
    echo ⚠️  Archivo .env.development no encontrado, usando valores por defecto
)

REM Cargar variables locales si existen
if exist .env.local (
    echo ✓ Cargando variables locales...
    for /f "tokens=*" %%i in (.env.local) do set %%i
)

echo.
echo 🔨 Construyendo e iniciando servicios...
docker-compose up --build -d

echo.
echo ⏳ Esperando que los servicios estén listos...
timeout /t 15 /nobreak > nul

echo.
echo 📊 Estado de los servicios:
docker-compose ps

echo.
echo ===================================
echo  ENTORNO DE DESARROLLO LISTO
echo ===================================
echo.
echo 🌐 URLs de acceso:
echo    Frontend: http://localhost
echo    API: http://localhost/api
echo    BackOffice: http://localhost/admin
echo    OnFire Academy: http://localhost/onfire-academy
echo    Health Check: http://localhost/health
echo    Dev Info: http://localhost/dev-info
echo.
echo 📝 Comandos útiles:
echo    Ver logs: logs.bat
echo    Parar servicios: stop-services.bat
echo    Reiniciar: restart-services.bat
echo.
echo ¿Abrir el navegador? (S/N)
set /p choice="Opción: "
if /i "%choice%"=="S" start http://localhost

pause