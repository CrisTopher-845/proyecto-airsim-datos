@echo off
title Orquestador Docker - AirSim
echo ===================================================
echo [DOCKER] Limpiando contenedores anteriores...
echo ===================================================
docker --context desktop-linux rm -f airsim-python-orquestador
echo.
echo ===================================================
echo [DOCKER] Levantando mision con Docker Compose...
echo ===================================================
cd /d "%~dp0"
docker --context desktop-linux compose up
echo.
echo [DOCKER] Proceso terminado.
pause
