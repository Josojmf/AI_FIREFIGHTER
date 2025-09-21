@echo off
title AI Firefighter - Stop All Services
echo ========================================
echo  DETENIENDO TODOS LOS SERVICIOS
echo ========================================
echo.

echo Cerrando servicios...

REM Detener Nginx
echo [1/4] Deteniendo Nginx...
taskkill /f /im nginx.exe 2>nul
if %errorlevel% equ 0 echo ✓ Nginx detenido

REM Detener Python (Frontend)
echo [2/4] Deteniendo Frontend (Python)...
taskkill /f /im python.exe 2>nul
if %errorlevel% equ 0 echo ✓ Frontend detenido

REM Detener Node.js (Backend + BackOffice)
echo [3/4] Deteniendo Backend y BackOffice (Node.js)...
taskkill /f /im node.exe 2>nul
if %errorlevel% equ 0 echo ✓ Backend y BackOffice detenidos

REM Cerrar ventanas de comando abiertas
echo [4/4] Cerrando ventanas de terminal...
taskkill /f /fi "WINDOWTITLE eq Frontend-Flask*" 2>nul
taskkill /f /fi "WINDOWTITLE eq Backend-API*" 2>nul
taskkill /f /fi "WINDOWTITLE eq BackOffice-React*" 2>nul
taskkill /f /fi "WINDOWTITLE eq Nginx-Proxy*" 2>nul

echo.
echo ========================================
echo  TODOS LOS SERVICIOS DETENIDOS
echo ========================================
echo.
echo Para reiniciar: start-all.bat
echo.
pause