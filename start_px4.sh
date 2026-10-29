#!/bin/bash
echo "[SYSTEM] Iniciando PX4 SITL (sin entorno visual)..."

PX4_DIR="${HOME}/PX4-Autopilot"
if [ ! -d "${PX4_DIR}" ]; then
    echo "[ERROR] No se encontró el directorio PX4-Autopilot en: ${PX4_DIR}"
    echo "Por favor ejecute primero: ./setup_linux.sh o clone PX4 en ~/PX4-Autopilot"
    read -p "Presione Enter para salir..."
    exit 1
fi

cd "${PX4_DIR}"
export PX4_SIM_HOSTNAME=127.0.0.1
make px4_sitl none_iris

echo "[ERROR] El simulador se ha cerrado."
read -p "Presione Enter para salir..."
