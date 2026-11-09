# PX4 como Arquitectura de Vuelo Autónomo (Estándar Primario)

## 1. Contexto y Justificación
El proyecto comenzó con la adopción de **PX4** como el controlador de vuelo autónomo primario y fundacional. Su elección se basó en su altísimo prestigio dentro del entorno académico, de investigación de robótica aérea, y su adopción estandarizada en la industria aeronáutica comercial (Auterion, Yuneec, entre otros). 

Toda la arquitectura de simulación original del proyecto (AirSim + Unreal Engine + scripts Python) se estructuró y diseñó para interactuar nativamente con las exigencias de red y seguridad propias de PX4. Esto nos ha permitido validar con éxito la viabilidad del concepto de *Digital Twin* (Gemelo Digital) realizando vuelos sin intervención humana en modalidad **OFFBOARD**.

---

## 2. ¿Qué es PX4 y por qué es el estándar del proyecto?
PX4 es un software de control de vuelo de código abierto enfocado fuertemente en desarrolladores de sistemas robóticos y flotas de drones autónomos. Sus características técnicas dictaron la forma en que se construyó nuestra estación terrena.

### 2.1 Estandarización MAVLink y API Orientada a Desarrolladores
PX4 basa todas sus telecomunicaciones externas en el protocolo MAVLink. Sin embargo, su mayor fortaleza radica en el **Modo OFFBOARD**. 

> [!TIP]
> El modo OFFBOARD está específicamente diseñado desde su base para ceder el control total del vehículo a un computador externo (Companion Computer). En lugar de seguir una ruta pregrabada de forma estática, PX4 delega las decisiones a nuestro código en Python, quien le inyecta coordenadas, velocidades o trayectorias calculadas en milisegundos basándose en factores externos, haciendo a este firmware ideal para sistemas robóticos complejos.

### 2.2 Estimación de Estado (EKF2)
PX4 emplea filtros *Extended Kalman Filter* de segunda generación (EKF2) que logran una fusión de sensores de grado investigativo. Procesa y reconcilia datos conflictivos entre la IMU, GPS, Magnetómetros y Odometría Visual con una precisión extrema, lo que se traduce en un vuelo simulado hiperrealista frente a ráfagas de viento y colisiones en Unreal Engine.

---

## 3. Hardware Compatible (El Ecosistema Pixhawk)
A diferencia de sistemas multipropósito, el despliegue físico de PX4 se recomienda y certifica sobre la familia de hardware **Pixhawk FMU** (Flight Management Unit). Esta rigidez asegura que el código probado en el simulador se comporte exactamente igual en el mundo real.

* **Soluciones de Grado Industrial (Holybro & CUAV)**: Placas como Pixhawk 6C o Pixhawk 6X son el hardware de referencia global para desplegar PX4.
* **Kits de Desarrollo Robótico**: La transición de la simulación a un dron físico se realiza generalmente a través de plataformas pre-ensambladas y estandarizadas como el *Holybro X500 V2*. Estos kits minimizan los problemas eléctricos o de vibración mecánica, permitiendo a los investigadores enfocarse netamente en la programación de inteligencia artificial o visión computacional de alto nivel.

---

## 4. Integración Práctica con la Arquitectura del Proyecto
La integración de PX4 exige configuraciones estrictas, tanto a nivel de sincronización temporal en la simulación, como en la lógica de seguridad programática.

### 4.1 Modificación en el Entorno Virtual (AirSim)
Para que el motor Unreal Engine funcione en simbiosis con PX4, el archivo `settings.json` debe habilitar el modo **LockStep**.

> [!IMPORTANT]
> El LockStep congela virtualmente el tiempo en el simulador hasta que PX4 confirme que ha terminado de procesar los datos de los sensores. Esto asegura que el simulador y el dron jamás se desincronicen, incluso si el PC sufre caídas de fotogramas por segundo (FPS).

Configuración requerida en `settings.json`:
```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "ClockType": "SteppableClock",
  "Vehicles": {
    "PX4": {
      "VehicleType": "PX4Multirotor",
      "UseSerial": false,
      "LockStep": true,
      "UseTcp": true,
      "TcpPort": 4560,
      "ControlPort": 14580,
      "LocalHostIp": "127.0.0.1"
    }
  }
}
```

### 4.2 Ejecución del Entorno SITL (Linux / Ubuntu)
La inicialización de PX4 en simulación requiere invocar el compilador nativo desde el directorio raíz del firmware dentro de Ubuntu:

```bash
cd ~/PX4-Autopilot
export PX4_SIM_HOSTNAME=127.0.0.1
make px4_sitl none_iris
```
Al iniciarse, PX4 buscará automáticamente conectarse a AirSim mediante el puerto TCP `4560` y expondrá el puerto de telemetría UDP `14540`, el cual será consumido por nuestros scripts en Python.

### 4.3 Modificaciones y Lógica Restrictiva de Control (PyMavlink)
Controlar a PX4 programáticamente exige el estricto cumplimiento de medidas de seguridad (*failsafes*):

1. **Inyección de Setpoints Previa**: Para que PX4 acepte el comando de entrar en modo OFFBOARD, es un requisito técnico obligatorio que el script le inyecte coordenadas de destino de forma continua (al menos durante 1 segundo) *antes* de solicitar el cambio de modo.
2. **Transmisión Ininterrumpida**: Una vez en vuelo, el script debe enviar un setpoint a una tasa mayor a 2 Hz. Si Python deja de enviar coordenadas por más de 500 ms, PX4 activará un failsafe de emergencia y abortará la misión.
3. **Comportamiento Espacial Nativo**: En Offboard, PX4 obedece vectores espaciales fluidos. Si se le envía una coordenada Z negativa (convención NED para altitud), el vehículo encenderá rotores y ascenderá de forma fluida hacia ese punto, sin requerir un comando `TAKEOFF` literal.
4. **Tipado Estricto Float**: La librería rechaza enteros. Es forzoso definir comandos con punto decimal (`0.0`).
5. **Sincronización de Armado Robusta**: Se erradicaron comandos forzados (force arm). Ahora el sistema utiliza el comando de armado estándar puro, seguido de una validación telemétrica (`master.motors_armed_wait()`) para garantizar despegues 100% seguros y validados por el propio dron.

---

## 5. Código Orquestador Consolidado (`mision_autonoma.py`)

A continuación, la versión final adaptada de la misión, compatible con el ecosistema **Dockerizado**, rutinas Failsafe (Ctrl+C), flujo ininterrumpido de setpoints y exposición correcta de red a `0.0.0.0`.

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

# Configuración de logs de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

ALTURA_SEGURA = -115.0  # Altitud de seguridad en metros (NED)
ARCHIVO_LOG = "mision_mapeo_final.csv"

grabando_telemetria = True
telemetria_actual = { "tiempo": 0, "x": 0.0, "y": 0.0, "z": 0.0, "vel_x": 0.0, "vel_y": 0.0 }
target_actual = { "x": 0.0, "y": 0.0, "z": 0.0 }

# --- CONEXIÓN MAVLINK ---
print("[MAVLINK] Esperando conexión de PX4 SITL...")
# En Docker usamos udpout al puerto 14580 (donde PX4 escucha en modo Onboard)
master = mavutil.mavlink_connection('udpout:host.docker.internal:14580', source_system=254)

print("[MAVLINK] Abriendo túnel UDP hacia el host... (Esperando heartbeat)")
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
    """Hilo encargado de la telemetría y transmisión obligatoria de Setpoints para modo OFFBOARD"""
    global grabando_telemetria, telemetria_actual
    start_time = time.time()
    
    while grabando_telemetria:
        try:
            with open(ARCHIVO_LOG, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Tiempo(s)", "X", "Y", "Z", "Vel_X", "Vel_Y"])
                
                while grabando_telemetria:
                    # REQUISITO PX4: Transmisión continua a alta frecuencia
                    master.mav.set_position_target_local_ned_send(
                        0, master.target_system, master.target_component,
                        mavutil.mavlink.MAV_FRAME_LOCAL_NED, int(0b110111111000), 
                        target_actual["x"], target_actual["y"], target_actual["z"],
                        0, 0, 0, 0, 0, 0, 0, 0
                    )
                    
                    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
                    if msg:
                        t = round(time.time() - start_time, 2)
                        writer.writerow([t, msg.x, msg.y, msg.z, msg.vx, msg.vy])
                        telemetria_actual.update({"tiempo": t, "x": round(msg.x, 2), "y": round(msg.y, 2), "z": round(msg.z, 2)})
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
    global grabando_telemetria
    time.sleep(2) 
    
    try:
        print("[FLIGHT_CTRL] Solicitando modo de vuelo: OFFBOARD (PX4)")
        master.mav.command_long_send(master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE, 0, 209.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        time.sleep(1)

        print("[FLIGHT_CTRL] Enviando comando de armado (ARM_DISARM)...")
        armado = False
        while not armado:
            master.mav.command_long_send(
                master.target_system, master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            )
            msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=5.0)
            if msg and (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                armado = True
                print("[FLIGHT_CTRL] Motores armados exitosamente.")
            else:
                time.sleep(1)

        print(f"[NAV] Ascenso automático OFFBOARD hacia: {abs(ALTURA_SEGURA)}m")
        target_actual["z"] = ALTURA_SEGURA
        navegar_a_punto(0, 0, ALTURA_SEGURA, tolerancia=2.0)

        puntos_ruta = [(200.0, 0.0, ALTURA_SEGURA), (200.0, 200.0, ALTURA_SEGURA), (0.0, 200.0, ALTURA_SEGURA), (0.0, 0.0, ALTURA_SEGURA)]
        for pt in puntos_ruta:
            navegar_a_punto(pt[0], pt[1], pt[2])

        print("[FLIGHT_CTRL] Misión completada. Iniciando secuencia de aterrizaje.")
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        )
        
        while telemetria_actual["z"] < -1.0:
            time.sleep(0.5)
            
        time.sleep(3)
        grabando_telemetria = False
        print("[SYSTEM] Vuelo finalizado.")
    except Exception as e:
        grabando_telemetria = False 

def activar_failsafe_rtl():
    print("\n[EMERGENCIA] Abortando misión y enviando comando RTL...")
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
    
    puerto_actual = 5001
    while puerto_actual < 5020: 
        try:
            print(f"[GCS] Estación Terrena activa en: http://127.0.0.1:{puerto_actual}")
            app.run(host='0.0.0.0', port=puerto_actual, use_reloader=False)
            break
        except OSError:
            puerto_actual += 1
```
