#!/bin/bash
echo "[SYSTEM] Iniciando PX4 SITL..."
cd ~/PX4-Autopilot
export PX4_SIM_HOSTNAME=127.0.0.1
make px4_sitl none_iris

# Si el comando falla o se cierra, mantener la consola abierta
echo "[ERROR] El simulador se ha cerrado."
read -p "Presione Enter para salir..."

