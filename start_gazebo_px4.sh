#!/bin/bash
echo "[SYSTEM] Iniciando Gazebo y PX4 SITL con LiDAR..."

# 1. Cargar ROS 2 si está instalado (opcional para plugins ROS)
if [ -f /opt/ros/humble/setup.bash ]; then
    source /opt/ros/humble/setup.bash
    export ROS_LOCALHOST_ONLY=1
fi

export LC_ALL=C
export LANG=C
export PX4_SIM_HOSTNAME=127.0.0.1
export GAZEBO_IP=127.0.0.1

# Desactivar LOCKSTEP estricto para evitar congelamiento de la física y ventana de Gazebo
export PX4_LOCKSTEP=0

# Configurar DISPLAY para entorno gráfico (Nativo o WSL)
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:0
fi

# 2. Definir rutas relativas dinámicas (¡Funciona en cualquier instalación de Linux!)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}"
CUSTOM_MODELS_DIR="${PROJECT_DIR}/custom_models"
CAVE_MODELS_DIR="${PROJECT_DIR}/gazebo_cave_world/worlds/models"
CAVE_WORLD="${PROJECT_DIR}/gazebo_cave_world/worlds/cave_world.world"

# 3. Localizar PX4-Autopilot en el home del usuario
PX4_DIR="${HOME}/PX4-Autopilot"
if [ ! -d "${PX4_DIR}" ]; then
    echo "[ERROR] No se encontró el directorio PX4-Autopilot en: ${PX4_DIR}"
    echo "Por favor ejecute primero: ./setup_linux.sh o clone PX4 en ~/PX4-Autopilot"
    read -p "Presione Enter para salir..."
    exit 1
fi

cd "${PX4_DIR}"

# 4. Exportar rutas de modelos de Gazebo
export GAZEBO_MODEL_PATH="${CUSTOM_MODELS_DIR}:${CAVE_MODELS_DIR}:${GAZEBO_MODEL_PATH}"

# Timeout suficiente para que Gazebo cargue los meshes 3D de la cueva
export PX4_SIMULATOR_TIMEOUT=300

# 5. Configurar el mundo personalizado
export PX4_SITL_WORLD="${CAVE_WORLD}"

# Coordenadas seguras de spawn dentro de la cueva
export PX4_SITL_X=10.0
export PX4_SITL_Y=-22.0
export PX4_SITL_Z=1.0

# 6. Lanzar PX4 SITL con Gazebo Classic y sensor LiDAR
echo "[SYSTEM] Ejecutando make px4_sitl gazebo-classic_iris_rplidar..."
echo "[SYSTEM] GAZEBO_MODEL_PATH=${GAZEBO_MODEL_PATH}"
make px4_sitl gazebo-classic_iris_rplidar

echo "[INFO] El simulador se ha cerrado."
read -p "Presione Enter para salir..."
