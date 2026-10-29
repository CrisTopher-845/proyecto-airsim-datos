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
echo -e "\n${YELLOW}[1/5] Configurando permisos de ejecución...${NC}"
chmod +x *.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
chmod +x scratch/*.py 2>/dev/null || true
chmod +x scratch/*.sh 2>/dev/null || true
echo -e "${GREEN}Permisos configurados.${NC}"

# 2. Paquetes del Sistema Operativo
echo -e "\n${YELLOW}[2/5] Instalando paquetes base del sistema (apt)...${NC}"
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
    mesa-utils \
    libgl1-mesa-glx

# 3. Dependencias de Python
echo -e "\n${YELLOW}[3/5] Instalando librerías de Python requeridas...${NC}"
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# 4. Verificación e Instalación de PX4-Autopilot
PX4_DIR="${HOME}/PX4-Autopilot"
echo -e "\n${YELLOW}[4/5] Verificando PX4-Autopilot en ${PX4_DIR}...${NC}"

if [ ! -d "${PX4_DIR}" ]; then
    echo -e "${YELLOW}PX4-Autopilot no encontrado en ${PX4_DIR}.${NC}"
    read -p "¿Desea clonar PX4-Autopilot v1.14.3 automáticamente? (s/n): " RESP
    if [[ "$RESP" =~ ^[sSyY]$ ]]; then
        echo -e "${BLUE}Clonando PX4-Autopilot v1.14.3 recursivamente...${NC}"
        git clone https://github.com/PX4/PX4-Autopilot.git --recursive -b v1.14.3 "${PX4_DIR}"
        
        echo -e "${BLUE}Ejecutando script oficial de configuración de PX4 para Ubuntu...${NC}"
        bash "${PX4_DIR}/Tools/setup/ubuntu.sh" --no-nuttx --no-sim-tools
    else
        echo -e "${RED}Aviso: Deberás tener PX4-Autopilot instalado en ~/PX4-Autopilot para volar.${NC}"
    fi
else
    echo -e "${GREEN}PX4-Autopilot ya está presente en ${PX4_DIR}.${NC}"
fi

# 5. Aplicar parches del proyecto en PX4
if [ -d "${PX4_DIR}" ]; then
    echo -e "\n${YELLOW}[5/5] Aplicando parches y configuraciones de vuelo a PX4...${NC}"
    python3 "${SCRIPT_DIR}/scripts/apply_px4_patches.py"
else
    echo -e "\n${YELLOW}[5/5] Omitiendo parches de PX4 (directorio no disponible).${NC}"
fi

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN} ¡TODO LISTO! EL ENTORNO ESTÁ COMPLETAMENTE CONFIGURADO EN LINUX    ${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "Para iniciar el proyecto en Linux:"
echo -e "  1. Simulación 3D (Gazebo + PX4 + Cueva):  ${YELLOW}./start_gazebo_px4.sh${NC}"
echo -e "  2. Misión y Tablero Web de Telemetría:    ${YELLOW}python3 mision_autonoma.py${NC}"
echo -e "  3. Ensamblar mapa de puntos 3D (.ply):    ${YELLOW}python3 ensamblar_mapa.py${NC}"
echo -e "${BLUE}====================================================================${NC}\n"

