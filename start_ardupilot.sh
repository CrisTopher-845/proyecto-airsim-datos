#!/bin/bash

# Exportar el PATH manualmente para que encuentre sim_vehicle.py y mavproxy.py
export PATH=$PATH:$HOME/.local/bin:$HOME/ardupilot/Tools/autotest

echo "[SYSTEM] Iniciando ArduPilot SITL..."
cd ~/ardupilot/ArduCopter

# Ejecutar el simulador apuntando a AirSim en localhost
# NOTA: --map fue eliminado por incompatibilidad cv2/numpy
sim_vehicle.py -v ArduCopter -f airsim-copter --console --out=127.0.0.1:14550

# Si el comando falla o se cierra, mantener la consola abierta para ver el error
echo "[ERROR] El simulador se ha cerrado."
read -p "Presione Enter para salir..."
