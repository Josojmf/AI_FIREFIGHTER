@echo off
title AI Firefighter - Complete System
echo ========================================
echo  AI FIREFIGHTER - SISTEMA COMPLETO
echo ========================================
echo.

echo [1/3] Iniciando Frontend...
start "Frontend" cmd /k "cd FO && python main.py"
timeout /t 4 /nobreak > nul

echo [2/3] Iniciando Backend...
start "Backend" cmd /k "cd api && node server.js"
timeout /t 4 /nobreak > nul

echo [3/3] Iniciando BackOffice...
start "BackOffice" cmd /k "cd BO && npm run dev -- --port 3001"

echo.
echo ========================================
echo  SISTEMA FUNCIONANDO
echo ========================================
echo.
echo URLs disponibles:
echo  Frontend:   http://localhost:8000
echo  Backend:    http://localhost:5000
echo  BackOffice: http://localhost:3001
echo.
echo Dominios configurados en hosts:
echo  Frontend:   http://onfire.local:8000
echo  Backend:    http://api.onfire.local:5000
echo  BackOffice: http://admin.onfire.local:3001
echo.

timeout /t 5 /nobreak > nul
start http://localhost:8000

pause
