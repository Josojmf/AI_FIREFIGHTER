@echo off
echo Deteniendo sistema...
taskkill /f /im python.exe 2>nul
taskkill /f /im node.exe 2>nul
echo Sistema detenido
pause
