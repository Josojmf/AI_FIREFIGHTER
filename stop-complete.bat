@echo off
echo Deteniendo sistema completo...

nginx -s quit 2>nul
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul

echo Todos los servicios detenidos
pause