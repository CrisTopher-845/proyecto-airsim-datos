# Sistema Autónomo de Navegación, Mapeo LiDAR y Telemetría en Entornos Subterráneos

Proyecto de simulación, telemetría y navegación autónoma para vehículos aéreos no tripulados (drones) en entornos subterráneos y cavernas utilizando **PX4 SITL**, **Gazebo Classic**, sensores **LiDAR** y una estación terrena web con **Flask**.

---

## 📋 Arquitectura del Sistema

- **Simulador Físico 3D:** Gazebo Classic con mundo de cueva subterránea optimizado (`gazebo_cave_world`).
- **Piloto Automático:** PX4-Autopilot (v1.14.3) en modo Software In The Loop (SITL).
- **Vehículo y Carga Útil:** Cuadricóptero Iris equipado con sensor RPLIDAR (`custom_models/iris_with_lidar`).
- **Control y Misión:** Navegación por puntos (Waypoints) mediante MAVLink (`pymavlink`) en modo OFFBOARD con protocolo de emergencia RTL (Return To Launch).
- **Estación Terrena Web:** Tablero en tiempo real con Flask, Leaflet (mapas offline integrados en `static/tiles`) y Chart.js.
- **Procesamiento de Nubes de Puntos:** Fusión y filtrado voxel con `Open3D` (`ensamblar_mapa.py`).

---

## 🚀 Guía Rápida de Instalación en Linux (Ubuntu 22.04 / 20.04)

### 1. Clonar el repositorio
Abre una terminal en tu entorno Linux y ejecuta:
```bash
git clone https://github.com/CrisTopher-845/proyecto-airsim-datos.git
cd proyecto-airsim-datos
```

### 2. Ejecutar el instalador automatizado
Hemos incluido un script (`setup_linux.sh`) que instala todas las dependencias del sistema, librerías de Python, verifica PX4-Autopilot y aplica automáticamente los parches necesarios:
```bash
chmod +x setup_linux.sh
./setup_linux.sh
```

El script configurará:
- Paquetes base (`build-essential`, `cmake`, `python3-pip`, etc.).
- Librerías de Python (`Flask`, `pymavlink`, `open3d`, `numpy`, `requests`).
- Clonación y configuración de PX4-Autopilot v1.14.3 (si aún no lo tienes instalado).
- Parches de spawn en la cueva (`PX4_SITL_X/Y/Z`) y silenciamiento de logs redundantes.

---

## 🕹️ Instrucciones de Ejecución

### Terminal 1: Iniciar el Simulador Gazebo y PX4 SITL
Lanza Gazebo con el escenario de la cueva y el dron equipado con LiDAR:
```bash
./start_gazebo_px4.sh
```
*(Gazebo cargará el mundo `cave_world.world` y posicionará el dron en las coordenadas seguras de despegue).*

### Terminal 2: Iniciar la Misión Autónoma y Estación Terrena
En una segunda terminal, lanza el software de control y monitoreo:
```bash
python3 mision_autonoma.py
```
- Se conectará vía MAVLink con PX4 en el puerto `14540`.
- Iniciará el despegue automático y navegación por la cueva.
- Abrirá automáticamente la interfaz web en tu navegador: **`http://127.0.0.1:5001`**
- Registrará la telemetría en tiempo real en `mision_mapeo_final.csv`.
- Presionar `Ctrl + C` en cualquier momento aborta de forma segura enviando la orden de retorno a casa (**RTL**).

### Terminal 3 (Opcional): Generar Mapa 3D Global
Si capturaste fotogramas LiDAR en la carpeta `dataset_lidar/`, genera la nube de puntos fusionada ejecutando:
```bash
python3 ensamblar_mapa.py
```
El archivo de salida `mapa_global_perfecto.ply` puede abrirse en **CloudCompare**, **MeshLab** o **Blender**.

---

## 📁 Estructura del Repositorio

```text
├── custom_models/                  # Modelos personalizados de Gazebo (Iris con LiDAR)
├── gazebo_cave_world/              # Mundo 3D de cueva, mallas (.obj) y texturas optimizadas
│   ├── worlds/                     # Archivos de mundo Gazebo (.world)
│   └── worlds/models/cave_world/   # Mallas 3D y colisiones optimizadas
├── static/                         # Archivos estáticos de la interfaz web
│   ├── chart.js                    # Gráficos de telemetría
│   ├── leaflet.js / leaflet.css    # Motor de mapa interactivo
│   └── tiles/                      # Cuadrículas de mapa OpenStreetMap offline
├── templates/                      # Vistas HTML (index.html del tablero web)
├── scripts/                        # Scripts auxiliares y parches automáticos
│   └── apply_px4_patches.py        # Parcheador de PX4 (spawn y plugins)
├── scratch/                        # Scripts de análisis, pruebas y utilidades de malla
├── mision_autonoma.py              # Script principal de vuelo autónomo y servidor GCS
├── mision_ardupilot.py             # Script alternativo para ArduPilot SITL
├── start_gazebo_px4.sh             # Lanzador principal de Gazebo + PX4 en Linux
├── start_px4.sh                    # Lanzador rápido de PX4 SITL sin interfaz visual
├── setup_linux.sh                  # Instalador automatizado de dependencias para Linux
├── requirements.txt                # Dependencias de Python
└── README.md                       # Documentación principal
```

---

## 🛠️ Requisitos Técnicos

- **Sistema Operativo:** Ubuntu 22.04 LTS (o WSL2 con Ubuntu 22.04).
- **Python:** 3.8 o superior.
- **Gazebo:** Gazebo Classic 11.
- **PX4 Autopilot:** v1.14.3 (recomendado).

