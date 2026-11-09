# Códigos y Arquitectura de Software del Proyecto

## 1. Contexto y Propósito de la Transición
En las fases iniciales de simulación y pruebas, el control del vehículo aéreo no tripulado (UAV) se gestionó mediante **QGroundControl (QGC)**, una estación de control terrestre (GCS) basada en una Interfaz Gráfica de Usuario (GUI). Aunque esta herramienta es ideal para operaciones manuales y validación rápida, el alcance del proyecto requirió migrar hacia un entorno de ejecución programático basado en Python.

El propósito de esta transición fue eliminar la dependencia de la intervención humana en la planificación de rutas, permitiendo que el dron ejecute misiones de manera autónoma, escalable y capaz de reaccionar dinámicamente a los datos del entorno.

---

## 2. Análisis del Entorno Visual: QGroundControl
QGroundControl se utilizó para las primeras simulaciones debido a su accesibilidad y diseño visual.

* **Metodología:** La planificación de misiones se realiza mediante la colocación manual de waypoints sobre un mapa interactivo.
* **Ventajas:** Curva de aprendizaje baja, excelente representación espacial y telemetría visual inmediata.

### Limitaciones para el proyecto:
* **Rigidez:** Las misiones son estáticas; una vez cargado el plan de vuelo, es difícil alterar la ruta automatizadamente basándose en variables externas.
* **Intervención Manual:** Requiere que un operador interactúe con la interfaz para cada vuelo.
* **Aislamiento de Datos:** Dificulta la ingesta de telemetría en tiempo real hacia otros scripts u bases de datos para su análisis.

---

## 3. Justificación del Enfoque Programático: Python
La implementación de scripts en Python transforma al dron de un simple vehículo teledirigido a un nodo de un sistema informático complejo.

* **Automatización Total:** Permite la ejecución de misiones de principio a fin (armado, despegue, recorrido y aterrizaje) ejecutando un solo script, garantizando repetibilidad milimétrica.
* **Lógica Condicional Dinámica:** Permite insertar bucles y condicionales. El dron puede tomar decisiones en tiempo real (ej. cambiar de altitud o abortar la misión) si los sensores reportan anomalías.
* **Integración y Escalabilidad:** Facilita la conexión directa de los datos de vuelo con otras bibliotecas de análisis o algoritmos de Inteligencia Artificial.

---

## 4. Códigos y Scripts Implementados
Para lograr un sistema integral y desacoplado, la arquitectura se dividió en dos capas principales: una interfaz de visualización (**Frontend HTML**) y un entorno de control lógico (**Backend Python**).

### 4.1. Capa de Visualización y Dashboard (Código `.html`)
**¿Por qué HTML?** Separar la visualización gráfica de la lógica de vuelo permite que cualquier supervisor pueda monitorear la misión desde un navegador web de forma remota.

Este archivo define la estructura visual (DOM). Actúa como un cliente pasivo que "escucha" y grafica en tiempo real los datos provenientes de Python, mostrando parámetros críticos (altitud, velocidad, coordenadas GPS) de forma limpia. 
*(El código fuente íntegro del dashboard se encuentra en el archivo `index.html`).*

### 4.2. Capa de Control Lógico (Código Python Antiguo - AirSim API)
En las primeras fases, se usó Python junto a la API nativa de AirSim.
* **Lógica de Vuelo:** Se conectaba directamente al motor gráfico para mover el dron.
* **Extracción de Datos:** Extraía la telemetría del entorno 3D y la enviaba al dashboard web.

> [!WARNING]
> Este enfoque original fue **abandonado** ya que la API de AirSim genera un movimiento irreal (paradas en seco y ausencia de inercia), alejándose de la física de un dron real.

---

## 5. Evolución de la Arquitectura (Integración de MAVLink y PX4)

Para elevar el rigor técnico del proyecto a estándares de la industria aeroespacial, se implementó una arquitectura de *Gemelo Digital* utilizando **MAVLink** en conjunto con el controlador de vuelo **PX4 SITL** dentro de Docker.

**Justificación de la Transición:**
1. **Desacoplamiento Estructural:** El entorno 3D (AirSim) ya no toma decisiones; solo renderiza y simula la física pura (gravedad, colisiones). El "cerebro" ahora es PX4.
2. **Control PID Real:** PX4 procesa la masa, inercias y aplica algoritmos PID para ajustar las RPM de los motores virtuales, logrando vuelos hiperrealistas (con sobreimpulsos reales en las curvas).
3. **Portabilidad de Hardware:** El script actual ignora si controla un videojuego o un dron físico real. Si la placa controladora se traslada a un vehículo físico, el código no requiere modificación alguna.

### 5.1. Capa de Control Lógico Actualizado (Código MAVLink)
Python actúa como la GCS. Transforma instrucciones de alto nivel y las transmite a PX4 mediante puertos UDP locales. 

* **Ejecución de Misiones (Modo OFFBOARD):** A través del puerto de red, inyecta un flujo constante de coordenadas (Setpoints) requerido por el protocolo de seguridad de PX4, fuerza el modo autónomo y guía al dron vectorialmente.
* **Extracción de Telemetría (Sensor Fusión):** En un hilo paralelo, escucha los paquetes `LOCAL_POSITION_NED` emitidos por PX4, los formatea y expone a través de una API REST (Flask) hacia el Dashboard HTML.

### 5.2. Complicaciones Técnicas Resueltas durante la Implementación
Durante el desarrollo del script final para PX4, superamos problemas críticos de integración:

1. **Enrutamiento de Puertos UDP:** La conexión por defecto `udpin:127.0.0.1:14550` solía entrar en conflicto con otras estaciones terrenas o con el contenedor Docker. Se migró a la conexión de puerto Onboard usando **UDP Hole Punching** (`udpout` al puerto `14580`) permitiendo atravesar el firewall de Docker sin colisiones.
2. **Tipado Estricto de C (Float vs Int):** La librería `pymavlink` posee validadores estrictos heredados de C. Al enviar comandos de armado con enteros (`0`, `1`), el script colapsaba con `struct.error: required argument is not a float`. Se solucionó forzando todos los argumentos a decimales (`0.0`, `1.0`).
3. **Lógica NED (Aterrizaje Prematuro):** El sistema coordenado NED (*North-East-Down*) invierte el eje Z (negativo hacia el cielo). El bucle de aterrizaje evaluaba erróneamente `z > -1.0`, provocando que el script finalizara mientras el dron seguía a 150 metros de altura. Se corrigió invirtiendo el operador lógico a `z < -1.0`.
4. **Condición de Carrera en Hilos (Thread Racing):** Se aislaron las lecturas del socket MAVLink al hilo de telemetría exclusivamente. El hilo de comando asume el éxito mediante esperas no bloqueantes o validaciones indirectas de estado.

### 5.3 Código Final Consolidado (PyMavlink robusto para PX4)
A continuación, la versión final adaptada de la misión, compatible con Docker, rutinas de Failsafe (Ctrl+C), flujo ininterrumpido de setpoints y exposición de red en `0.0.0.0`.

```python
import time
import csv
import threading
import logging
import math
import traceback
import signal
import sys
from pymavlink import mavutil
from flask import Flask, render_template, jsonify

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
ALTURA_SEGURA = -150.0  
ARCHIVO_LOG = "mision_mapeo_final.csv"

grabando_telemetria = True
telemetria_actual = { "tiempo": 0, "x": 0.0, "y": 0.0, "z": 0.0, "vel_x": 0.0, "vel_y": 0.0 }
target_actual = { "x": 0.0, "y": 0.0, "z": 0.0 }

# --- CONEXIÓN GLOBAL MAVLINK A PX4 DOCKERIZADO ---
print("[MAVLINK] Abriendo túnel UDP hacia el host... (Esperando heartbeat)")
master = mavutil.mavlink_connection('udpout:host.docker.internal:14580', source_system=254)

while True:
    master.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
    msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
    if msg:
        print("[MAVLINK] ¡Heartbeat recibido desde PX4!")
        break

master.target_system = 1
master.target_component = 1

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify(telemetria_actual)

def registrar_datos():
    """EL COPILOTO: Bucle de control activo. Mantiene flujo constante con PX4"""
    global grabando_telemetria, telemetria_actual
    start_time = time.time()
    
    while grabando_telemetria:
        try:
            with open(ARCHIVO_LOG, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Tiempo(s)", "X", "Y", "Z", "Vel_X", "Vel_Y"])
                
                while grabando_telemetria:
                    # OFFBOARD Mode en PX4 exige Setpoints constantes
                    master.mav.set_position_target_local_ned_send(
                        0, master.target_system, master.target_component,
                        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                        int(0b110111111000), 
                        target_actual["x"], target_actual["y"], target_actual["z"],
                        0, 0, 0, 0, 0, 0, 0, 0
                    )

                    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=False)
                    if msg:
                        t = round(time.time() - start_time, 2)
                        writer.writerow([t, msg.x, msg.y, msg.z, msg.vx, msg.vy])
                        telemetria_actual.update({"tiempo": t, "x": round(msg.x, 2), "y": round(msg.y, 2), "z": round(msg.z, 2)})
                        
                    time.sleep(0.1)
            break 
        except PermissionError:
            time.sleep(3)

def navegar_a_punto(target_x, target_y, target_z, tolerancia=4.0):
    target_actual.update({"x": float(target_x), "y": float(target_y), "z": float(target_z)})
    while grabando_telemetria:
        distancia = math.sqrt((target_actual["x"] - telemetria_actual["x"])**2 + (target_actual["y"] - telemetria_actual["y"])**2 + (target_actual["z"] - telemetria_actual["z"])**2)
        if distancia <= tolerancia:
            break
        time.sleep(0.1)

def ejecutar_vuelo():
    """EL PILOTO AUTOMÁTICO: Orquestación principal de misiones"""
    global grabando_telemetria
    time.sleep(4) 
    
    try:
        print("[Piloto] Cambiando a modo de vuelo autónomo (OFFBOARD) en PX4...")
        master.mav.command_long_send(master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE, 0, 209.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        time.sleep(1)

        print("[Piloto] Armando Motores...")
        while True:
            master.mav.command_long_send(
                master.target_system, master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            )
            msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=5.0)
            if msg and (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                print("[Piloto] Motores armados exitosamente.")
                break
            time.sleep(1)

        target_actual["z"] = ALTURA_SEGURA
        navegar_a_punto(0, 0, ALTURA_SEGURA, tolerancia=2.0)

        puntos_ruta = [(200.0, 0.0, ALTURA_SEGURA), (200.0, 200.0, ALTURA_SEGURA), (0.0, 0.0, ALTURA_SEGURA)]
        for pt in puntos_ruta:
            navegar_a_punto(pt[0], pt[1], pt[2])

        print("[Piloto] Misión completada. Iniciando Aterrizaje...")
        master.mav.command_long_send(master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        while telemetria_actual["z"] < -1.0:
            time.sleep(0.5)
            
        time.sleep(3)
        grabando_telemetria = False
    except Exception:
        grabando_telemetria = False 

def activar_failsafe_rtl():
    try:
        master.mav.command_long_send(master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, 0, 0, 0, 0, 0, 0, 0, 0)
    except Exception:
        pass

if __name__ == '__main__':
    def signal_handler(sig, frame):
        global grabando_telemetria
        grabando_telemetria = False
        activar_failsafe_rtl()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    threading.Thread(target=registrar_datos, daemon=True).start()
    threading.Thread(target=ejecutar_vuelo, daemon=True).start()
    
    app.run(host='0.0.0.0', port=5001, use_reloader=False)
```

---

## 6. Capa de Monitoreo y Verificación (QGroundControl)

**¿Por qué utilizamos QGroundControl en paralelo con Python?** 
QGroundControl (QGC) se integra como una Estación de Control Terrestre complementaria, enfocada exclusivamente en la telemetría visual y validación geoespacial. 

> [!TIP]
> Mientras el script de Python opera como el controlador lógico primario (Companion Computer), QGC actúa como un **auditor externo pasivo**. Esto permite visualizar el comportamiento del gemelo digital sin interferir en el bucle de control principal.

**Arquitectura de Red y Resolución de Puertos:** 
Para lograr la coexistencia de ambos sistemas de control sin generar colisiones de sockets (`WinError 10013`) ni bloqueos por conflictos de identidad en la red MAVLink, se aprovecha la capacidad de ruteo múltiple del controlador PX4. QGC consume los datos a través del puerto UDP estándar `14550`, mientras que el script de Python establece una conexión directa a través del puerto configurado para hardware complementario (`14580`).
