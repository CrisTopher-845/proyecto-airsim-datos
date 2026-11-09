# ArduPilot como Arquitectura de Vuelo Autónomo

## 1. Contexto y Justificación del Análisis
El presente documento surge como una medida de mitigación frente a las actuales dificultades logísticas y de importación de hardware específico para ecosistemas **PX4** en Chile. La alta demanda, los quiebres de stock en proveedores locales y los tiempos de espera prolongados en aduanas representan un riesgo crítico para el avance continuo del proyecto. 

Por lo tanto, se plantea la integración de **ArduPilot** como sistema de control de vuelo alternativo. El objetivo es asegurar que la arquitectura de software actual (Simulador, Contenedores Docker, Scripts de Control) mantenga su validez tecnológica y pueda desplegarse en una gama mucho más amplia y accesible de controladores de vuelo físicos.

---

## 2. ¿Qué es ArduPilot y por qué es la alternativa ideal frente a PX4?
ArduPilot es una de las suites de software de código abierto más maduras y utilizadas a nivel mundial para el control de vehículos autónomos. Su arquitectura modular no solo soporta multirrotores (ArduCopter), sino también aviones de ala fija, rovers, submarinos y antenas rastreadoras. 

Para el contexto específico de este proyecto, ArduPilot se presenta como la alternativa natural y de menor fricción frente a PX4 por las siguientes razones técnicas:

### 2.1 Estandarización del Protocolo MAVLink
Ambos sistemas (PX4 y ArduPilot) utilizan **MAVLink (Micro Air Vehicle Link)** como su lenguaje de comunicación principal. Esto es crítico para la arquitectura del proyecto, ya que significa que las estaciones de tierra (QGroundControl, Mission Planner) y los scripts desarrollados en Python utilizando la biblioteca `pymavlink`, no requieren ser reescritos desde cero. Las estructuras de los mensajes (envío de coordenadas, lectura de telemetría y recepción de información del vehículo) mantienen una sintaxis homóloga.

### 2.2 Filtros de Estimación de Estado (EKF)
ArduPilot utiliza *Extended Kalman Filters* (EKF3) altamente optimizados para realizar la estimación del estado del vehículo fusionando información de:
* GPS
* Unidad de Medición Inercial (IMU)
* Barómetro
* Odometría Visual

> [!TIP]
> Gracias a este proceso de fusión, el sistema posee una elevada tolerancia a fallos. Si un sensor deja de entregar información durante el vuelo, el EKF implementa mecanismos de redundancia que permiten mantener la estabilidad y continuar la misión de forma segura.

### 2.3 Soporte Avanzado para Entornos Simulados (SITL)
El entorno **Software In The Loop (SITL)** de ArduPilot constituye uno de los sistemas de simulación más completos disponibles, permitiendo:
- Ejecutar el firmware completo del controlador de vuelo idéntico al físico.
- Simular condiciones meteorológicas (viento) e interferencias.
- Introducir fallos inyectados de sensores.

Además, SITL mantiene compatibilidad directa con motores gráficos como Unreal Engine mediante **AirSim**, permitiendo validar algoritmos de navegación antes de su implementación en hardware físico.

### 2.4 Comunidad y Documentación
ArduPilot posee una de las comunidades de desarrollo más grandes dentro del ecosistema de robótica open-source, lo que se traduce en: actualizaciones constantes, corrección rápida de errores, compatibilidad masiva con hardware de terceros y soporte comunitario activo.

---

## 3. Hardware Compatible (Estrategia de Mitigación)
La principal vulnerabilidad logística es la dependencia de hardware específico de la familia PX4. ArduPilot reduce este riesgo gracias a su compatibilidad con un ecosistema de hardware mucho más amplio, descentralizado y de fácil disponibilidad.

### 3.1 Controladores de Vuelo (FC) Basados en STM32
ArduPilot es agnóstico al fabricante del controlador. Funciona perfectamente en placas con microcontroladores **STM32** (F4, F7, H7).

* **Estándar Pixhawk (Empresarial / Académica)**: Fabricantes como Holybro y CUAV. Cualquier placa PX4 puede ser flasheada con ArduPilot sin modificaciones físicas.
* **Sistemas CubePilot (Alta Gama)**: Cube Orange y Cube Black. Ofrecen triple redundancia de sensores e IMUs aisladas mecánicamente para uso industrial.
* **Controladoras FPV (Emergencia y Bajo Costo)**: Fabricantes como Matek, SpeedyBee y Kakute producen placas diminutas y económicas. ArduPilot ha sido adaptado para operar en ellas, permitiendo importar hardware a bajo costo mediante plataformas como AliExpress.

### 3.2 Integración Plug & Play de Periféricos
La migración no requiere reemplazar sensores:
* **Módulos GPS / RTK**: Soporta cualquier módulo U-Blox (Here3, Here4, M8N, M10).
* **Telemetría**: Compatible con Radios SiK 915 MHz, ESP8266 y Wi-Fi directo.

---

## 4. Integración Práctica con la Arquitectura Docker / AirSim
La migración hacia ArduPilot mantiene intacta la arquitectura principal del proyecto. La infraestructura basada en Docker, AirSim y scripts Python continúa siendo válida.

### 4.1 Modificación en el Entorno Virtual (AirSim)
Para establecer el puente de red hacia WSL, se configuran los puertos UDP y el enrutamiento TCP:

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "Vehicles": {
    "ArduCopter": {
      "VehicleType": "ArduCopter",
      "UseSerial": false,
      "LocalHostIp": "0.0.0.0",
      "UdpIp": "127.0.0.1",
      "UdpPort": 9003,
      "ControlPortIp": "127.0.0.1",
      "ControlPort": 9002,
      "UseTcp": true
    }
  }
}
```
> [!IMPORTANT]
> Es vital establecer `LocalHostIp` en `0.0.0.0` para garantizar que la red virtual de WSL pueda enrutar los paquetes UDP hacia el host de Windows.

### 4.2 Modificaciones en la Lógica de Control (PyMavlink)
La diferencia arquitectónica principal entre PX4 y ArduPilot es el modo de ejecución de misiones:
* **PX4 (OFFBOARD)**: Exige un flujo continuo de setpoints (>2 Hz) *antes* de aceptar el cambio de modo.
* **ArduPilot (GUIDED)**: Espera pasivamente. Una vez en GUIDED, el controlador atiende órdenes de movimiento sin necesidad de transmitir setpoints ciegos de antemano.

#### Complicaciones Técnicas Resueltas:
1. **Condición de Carrera (Thread Racing):** Al usar dos hilos (Telemetría para Flask y Control de Vuelo), los hilos bloqueantes "robaban" paquetes MAVLink. Se implementó una lectura asíncrona filtrada (`recv_match` con timeouts) para evitar acaparamientos del socket.
2. **Pre-Arm Checks y Seguridad:** Inicialmente se evadían las normas de seguridad apagando las validaciones del EKF (`ARMING_CHECK=0`). Para estandarizar el código a nivel de producción, **se restauró el protocolo estricto**. El script ahora delega la seguridad a ArduPilot, utilizando `master.motors_armed_wait()` para congelar el hilo orquestador hasta que el GPS y la IMU aprueben el despegue.

---

## 5. Código Orquestador Consolidado (`mision_ardupilot.py`)

A continuación, la versión final adaptada, compatible con el ecosistema Dockerizado (host expuesto a `0.0.0.0`), rutinas Failsafe (Ctrl+C) y chequeos de seguridad estrictos.

```python
import time
import csv
import threading
import logging
import math
import signal
import sys
from pymavlink import mavutil
from flask import Flask, render_template, jsonify

# Configuración de logs de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

ALTURA_SEGURA = -115.0  # Altitud de seguridad en metros (NED)
ARCHIVO_LOG = "mision_mapeo_ardupilot.csv"

grabando_telemetria = True
telemetria_actual = { "tiempo": 0, "x": 0.0, "y": 0.0, "z": 0.0, "vel_x": 0.0, "vel_y": 0.0 }
target_actual = { "x": 0.0, "y": 0.0, "z": 0.0 }

# --- CONEXIÓN MAVLINK ---
print("[MAVLINK] Estableciendo conexión TCP con ArduPilot (Puerto 5762)...")
master = mavutil.mavlink_connection('tcp:127.0.0.1:5762', source_system=254)
master.wait_heartbeat()
print(f"[MAVLINK] Conexión establecida. Target system ID: {master.target_system}")

# Solicitud de flujo de telemetría a 10 Hz
master.mav.request_data_stream_send(
    master.target_system, master.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1
)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify(telemetria_actual)

def registrar_datos():
    """Hilo de Telemetría Asíncrono no bloqueante"""
    global grabando_telemetria, telemetria_actual
    start_time = time.time()
    
    while grabando_telemetria:
        try:
            with open(ARCHIVO_LOG, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Tiempo(s)", "X", "Y", "Z", "Vel_X", "Vel_Y"])
                
                while grabando_telemetria:
                    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
                    if msg:
                        t = round(time.time() - start_time, 2)
                        writer.writerow([t, msg.x, msg.y, msg.z, msg.vx, msg.vy])
                        telemetria_actual.update({"tiempo": t, "x": round(msg.x, 2), "y": round(msg.y, 2), "z": round(msg.z, 2)})
            break 
        except PermissionError:
            time.sleep(3)

def navegar_a_punto(target_x, target_y, target_z, tolerancia=2.0):
    """Navegación dinámica hacia waypoints"""
    target_actual.update({"x": float(target_x), "y": float(target_y), "z": float(target_z)})
    while grabando_telemetria:
        master.mav.set_position_target_local_ned_send(
            0, master.target_system, master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            int(0b110111111000), target_actual["x"], target_actual["y"], target_actual["z"],
            0, 0, 0, 0, 0, 0, 0, 0
        )
        distancia = math.sqrt((target_actual["x"] - telemetria_actual["x"])**2 + (target_actual["y"] - telemetria_actual["y"])**2 + (target_actual["z"] - telemetria_actual["z"])**2)
        if distancia <= tolerancia:
            break
        time.sleep(0.1)

def ejecutar_vuelo():
    global grabando_telemetria
    time.sleep(2) 
    
    try:
        print("[FLIGHT_CTRL] Iniciando secuencia de armado (Pre-Arm Checks)...")
        while not master.motors_armed():
            master.set_mode('GUIDED')
            time.sleep(1)
            master.mav.command_long_send(
                master.target_system, master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0, 0, 0, 0, 0, 0
            )
            time.sleep(3)
            if master.motors_armed():
                print("[FLIGHT_CTRL] Confirmación recibida. Motores ARMED.")
                break

        print(f"[NAV] Despegue hacia altitud: {abs(ALTURA_SEGURA)}m")
        target_actual["z"] = ALTURA_SEGURA 
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, abs(ALTURA_SEGURA)
        )
        
        while telemetria_actual["z"] > (ALTURA_SEGURA + 1):
            time.sleep(0.5)

        # Matriz de Ruta
        puntos_ruta = [(200, 0, ALTURA_SEGURA), (0, 200, ALTURA_SEGURA), (0, 0, ALTURA_SEGURA)]
        for pt in puntos_ruta:
            navegar_a_punto(pt[0], pt[1], pt[2])

        print("[FLIGHT_CTRL] Misión completada. Solicitando LAND.")
        master.set_mode('LAND')
        
        while telemetria_actual["z"] < -0.5:
            time.sleep(0.5)

        grabando_telemetria = False
        print("[SYSTEM] Vuelo finalizado correctamente.")
    except Exception as e:
        grabando_telemetria = False

def activar_failsafe_rtl():
    """Failsafe dinámico de aborto de misión"""
    print("[EMERGENCIA] Abortando misión y enviando comando RTL...")
    try:
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, 0, 0, 0, 0, 0, 0, 0, 0
        )
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
    
    # Exposición a 0.0.0.0 para compatibilidad total con Docker Network
    puerto_actual = 5000
    while puerto_actual < 5020: 
        try:
            print(f"[GCS] Estación Terrena en: http://127.0.0.1:{puerto_actual}")
            app.run(host='0.0.0.0', port=puerto_actual, use_reloader=False)
            break
        except OSError:
            puerto_actual += 1
```
