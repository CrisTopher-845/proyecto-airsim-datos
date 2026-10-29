#!/bin/bash
# ==============================================================================
# Script de Instalación Automatizada de Dependencias para Linux (Ubuntu 22.04 / 20.04)
# Proyecto: Simulación Autónoma Drone PX4 + Gazebo Classic + Cueva 3D + LiDAR
# ==============================================================================

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${GREEN}   CONFIGURACIÓN Y DEPENDENCIAS DEL PROYECTO AIRSIM / PX4 EN LINUX   ${NC}"
echo -e "${BLUE}====================================================================${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# 1. Asegurar permisos de ejecución en todos los scripts
echo -e "\n${YELLOW}[1/6] Configurando permisos de ejecución...${NC}"
chmod +x *.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
chmod +x scratch/*.py 2>/dev/null || true
chmod +x scratch/*.sh 2>/dev/null || true
echo -e "${GREEN}Permisos configurados.${NC}"

# 2. Paquetes del Sistema Operativo
echo -e "\n${YELLOW}[2/6] Instalando paquetes base del sistema (apt)...${NC}"
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    cmake \
    git \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    wget \
    lsb-release \
    gnupg \
    mesa-utils \
    libgl1-mesa-glx

# 3. Instalación de Gazebo Classic 11
echo -e "\n${YELLOW}[3/6] Verificando e instalando Gazebo Classic 11...${NC}"
if ! command -v gazebo &> /dev/null; then
    echo -e "${BLUE}Instalando Gazebo 11 y librerías de desarrollo...${NC}"
    sudo apt-get install -y gazebo11 libgazebo11-dev
else
    echo -e "${GREEN}Gazebo Classic 11 ya está instalado ($(gazebo --version | head -n1)).${NC}"
fi

# 4. Dependencias de Python
echo -e "\n${YELLOW}[4/6] Instalando librerías de Python requeridas...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 5. Verificación e Instalación de PX4-Autopilot
PX4_DIR="${HOME}/PX4-Autopilot"
echo -e "\n${YELLOW}[5/6] Verificando PX4-Autopilot en ${PX4_DIR}...${NC}"

if [ ! -d "${PX4_DIR}" ]; then
    echo -e "${YELLOW}PX4-Autopilot no encontrado en ${PX4_DIR}.${NC}"
    read -p "¿Desea clonar PX4-Autopilot v1.14.3 automáticamente? (s/n): " RESP
    if [[ "$RESP" =~ ^[sSyY]$ ]]; then
        echo -e "${BLUE}Clonando PX4-Autopilot v1.14.3 recursivamente...${NC}"
        git clone https://github.com/PX4/PX4-Autopilot.git --recursive -b v1.14.3 "${PX4_DIR}"
        
        echo -e "${BLUE}Ejecutando script oficial de configuración de PX4 para Ubuntu...${NC}"
        bash "${PX4_DIR}/Tools/setup/ubuntu.sh" --no-nuttx
    else
        echo -e "${RED}Aviso: Deberás tener PX4-Autopilot instalado en ~/PX4-Autopilot para volar.${NC}"
    fi
else
    echo -e "${GREEN}PX4-Autopilot ya está presente en ${PX4_DIR}.${NC}"
fi

# 6. Aplicar parches del proyecto en PX4
if [ -d "${PX4_DIR}" ]; then
    echo -e "\n${YELLOW}[6/6] Aplicando parches y configuraciones de vuelo a PX4...${NC}"
    python3 "${SCRIPT_DIR}/scripts/apply_px4_patches.py"
else
    echo -e "\n${YELLOW}[6/6] Omitiendo parches de PX4 (directorio no disponible).${NC}"
fi

# 7. Opcional: Instalación de ROS 2 Humble si no está instalado
if [ ! -f /opt/ros/humble/setup.bash ]; then
    echo -e "\n${YELLOW}[OPCIONAL] ¿Deseas instalar ROS 2 Humble y sus plugins de Gazebo?${NC}"
    echo -e "Permite visualizar el sensor RPLIDAR a través de tópicos ROS /scan."
    read -p "¿Instalar ROS 2 Humble ahora? (s/n): " INST_ROS
    if [[ "$INST_ROS" =~ ^[sSyY]$ ]]; then
        echo -e "${BLUE}Configurando repositorios oficiales de ROS 2...${NC}"
        sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y ros-humble-desktop ros-humble-gazebo-ros-pkgs
        echo -e "${GREEN}ROS 2 Humble y Gazebo ROS packages instalados exitosamente.${NC}"
    fi
else
    echo -e "\n${GREEN}ROS 2 Humble ya está instalado en el sistema.${NC}"
fi

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN} ¡TODO LISTO! EL ENTORNO ESTÁ COMPLETAMENTE CONFIGURADO EN LINUX    ${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "Comandos de ejecución:"
echo -e "  1. Simulación 3D (Gazebo + PX4 + Cueva):  ${YELLOW}./start_gazebo_px4.sh${NC}"
echo -e "  2. Misión y Tablero Web de Telemetría:    ${YELLOW}python3 mision_autonoma.py${NC}"
echo -e "  3. Ensamblar mapa de puntos 3D (.ply):    ${YELLOW}python3 ensamblar_mapa.py${NC}"
echo -e "  4. Ver nubes de puntos 3D (Opcional):     ${YELLOW}sudo snap install cloudcompare${NC}"
echo -e "${BLUE}====================================================================${NC}\n"
