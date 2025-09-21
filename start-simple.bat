@echo off
title AI Firefighter - Simple Start
echo ========================================
echo  AI FIREFIGHTER - INICIO SIMPLE
echo ========================================
echo.

echo [1/3] Iniciando Frontend (Flask) en puerto 8000...
start "Frontend" cmd /k "cd FO && python main.py"
timeout /t 3 /nobreak > nul

echo [2/3] Iniciando Backend (API) en puerto 5000...
start "Backend" cmd /k "cd api && node server.js"
timeout /t 3 /nobreak > nul

echo [3/3] Iniciando BackOffice (React) en puerto 3001...
start "BackOffice" cmd /k "cd BO && npm run start"
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo  SERVICIOS INICIADOS
echo ========================================
echo.
echo URLs disponibles:
echo  Frontend:   http://localhost:8000
echo  Backend:    http://localhost:5000
echo  BackOffice: http://localhost:3001
echo.

timeout /t 10 /nobreak > nul
start http://localhost:8000

pause
