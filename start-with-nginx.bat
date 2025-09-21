@echo off
title AI Firefighter - Sistema Completo con Nginx
echo ========================================
echo  INICIANDO SISTEMA COMPLETO
echo ========================================

echo [1/4] Iniciando Frontend...
start "Frontend" cmd /k "cd FO && python main.py"
timeout /t 4 /nobreak > nul

echo [2/4] Iniciando Backend...
start "Backend" cmd /k "cd api && node server.js"
timeout /t 4 /nobreak > nul

echo [3/4] Iniciando BackOffice...
start "BackOffice" cmd /k "cd BO && npm run dev -- --port 3001"
timeout /t 8 /nobreak > nul

echo [4/4] Iniciando Nginx...
nginx -c nginx-simple.conf

echo.
echo ========================================
echo  SISTEMA LISTO
echo ========================================
echo.
echo Dominios con nginx:
echo  Frontend:   http://onfire.local
echo  BackOffice: http://admin.onfire.local
echo  API:        http://api.onfire.local
echo.

timeout /t 5 /nobreak > nul
start http://onfire.local

pause
