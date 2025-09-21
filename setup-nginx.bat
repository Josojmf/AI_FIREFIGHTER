@echo off
echo Configurando directorios y archivos para nginx...

REM Crear directorio logs si no existe
if not exist logs mkdir logs

REM Crear archivo error.log vacío
echo. > logs\error.log

REM Crear archivo access.log vacío  
echo. > logs\access.log

REM Crear archivo mime.types básico
echo text/html                             html htm shtml; > mime.types
echo text/css                              css; >> mime.types
echo text/xml                              xml; >> mime.types
echo application/javascript                js; >> mime.types
echo application/json                      json; >> mime.types
echo image/gif                             gif; >> mime.types
echo image/jpeg                            jpeg jpg; >> mime.types
echo image/png                             png; >> mime.types
echo image/svg+xml                         svg; >> mime.types
echo application/octet-stream              bin exe dll; >> mime.types

echo Configuración de nginx completada
echo.
echo Archivos creados:
echo  - logs/error.log
echo  - logs/access.log  
echo  - mime.types
echo.
echo Ahora puedes ejecutar: start-all.bat