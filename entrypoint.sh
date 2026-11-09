#!/bin/bash
set -e

echo "[DOCKER] Iniciando contenedor de orquestación..."
echo "[DOCKER] Entorno objetivo seleccionado: $ENTORNO_SITL"

if [ "$ENTORNO_SITL" = "PX4" ]; then
    echo "[DOCKER] Ejecutando misión para PX4..."
    python3 mision_autonoma.py
elif [ "$ENTORNO_SITL" = "ArduPilot" ]; then
    echo "[DOCKER] Configurando túneles de red TCP para ArduPilot..."
    # 1. Redirigir el MAVLink local 5762 del script hacia el host de Windows/WSL
    socat TCP-LISTEN:5762,fork TCP:host.docker.internal:5762 &
    
    # 2. (Eliminado: Redirección de puertos de Flask) Flask ya se encarga de exponerse en 0.0.0.0
    
    echo "[DOCKER] Ejecutando misión para ArduPilot..."
    python3 mision_ardupilot.py
else
    echo "[DOCKER][ERROR] Entorno '$ENTORNO_SITL' no reconocido. Usar 'PX4' o 'ArduPilot'."
    exit 1
fi
