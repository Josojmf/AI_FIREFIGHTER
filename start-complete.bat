@echo off
title AI Firefighter - Complete System
echo ========================================
echo  AI FIREFIGHTER - SISTEMA COMPLETO
echo ========================================
echo.

echo [1/4] Iniciando Frontend...
start "Frontend" cmd /k "cd FO && python main.py"
timeout /t 4 /nobreak > nul

echo [2/4] Iniciando Backend...
start "Backend" cmd /k "cd api && node server.js"
timeout /t 4 /nobreak > nul

echo [3/4] Iniciando BackOffice...
start "BackOffice" cmd /k "cd BO && npm run start"
timeout /t 6 /nobreak > nul

echo [4/4] Iniciando Nginx...
nginx -c nginx.conf

echo.
echo ========================================
echo  SISTEMA COMPLETO FUNCIONANDO
echo ========================================
echo.
echo URL PRINCIPAL: http://localhost
echo  Frontend:    http://localhost/
echo  API:         http://localhost/api/
echo  BackOffice:  http://localhost/admin/
echo  Health:      http://localhost/health
echo.

timeout /t 5 /nobreak > nul
start http://localhost

pause