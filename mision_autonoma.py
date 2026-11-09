import time
import csv
import threading
import logging
import math
import traceback
import signal
import sys
import airsim
from pymavlink import mavutil
from flask import Flask, render_template, jsonify

# Configuración de logs de Flask (suprimir advertencias menores)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# --- PARÁMETROS DE VUELO Y TELEMETRÍA ---
ALTURA_SEGURA = -115.0  # Altitud de seguridad en metros (convención NED)
ARCHIVO_LOG = "mision_mapeo_final.csv"

grabando_telemetria = True
telemetria_actual = { 
    "tiempo": 0, "x": 0.0, "y": 0.0, "z": 0.0, 
    "vel_x": 0.0, "vel_y": 0.0 
}
target_actual = { "x": 0.0, "y": 0.0, "z": 0.0 }

# --- CONEXIÓN MAVLINK ---
print("[MAVLINK] Esperando conexión de PX4 SITL...")
# En Docker usamos udpout al puerto 14580 (donde PX4 escucha en modo Onboard)
master = mavutil.mavlink_connection('udpout:host.docker.internal:14580', source_system=254)

# Enviar heartbeats continuamente hasta que PX4 responda (UDP Hole Punching)
print("[MAVLINK] Abriendo túnel UDP hacia el host... (Esperando heartbeat)")
while True:
    master.mav.heartbeat_send(mavutil.mavlink.MAV_TYPE_GCS, mavutil.mavlink.MAV_AUTOPILOT_INVALID, 0, 0, 0)
    msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
    if msg:
        print("[MAVLINK] ¡Heartbeat recibido desde PX4!")
        break

master.target_system = 1
master.target_component = 1
print(f"[MAVLINK] Conexión establecida. Target system ID: {master.target_system}")

# --- ENDPOINTS API LOCAL ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify(telemetria_actual)

# --- PROCESAMIENTO DE TELEMETRÍA Y SETPOINTS CONTINUOS ---
def registrar_datos():
    global grabando_telemetria, telemetria_actual
    print("[SYSTEM] Hilo de telemetría y transmisión de setpoints iniciado.")
    start_time = time.time()
    
    while grabando_telemetria:
        try:
            with open(ARCHIVO_LOG, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Tiempo(s)", "X", "Y", "Z", "Vel_X", "Vel_Y"])
                
                while grabando_telemetria:
                    # Transmisión continua del setpoint actual requerida por el modo OFFBOARD de PX4
                    master.mav.set_position_target_local_ned_send(
                        0, master.target_system, master.target_component,
                        mavutil.mavlink.MAV_FRAME_LOCAL_NED,
                        int(0b110111111000), 
                        target_actual["x"], target_actual["y"], target_actual["z"],
                        0, 0, 0, 0, 0, 0, 0, 0
                    )
                    
                    msg = master.recv_match(type='LOCAL_POSITION_NED', blocking=True, timeout=1.0)
                    if msg:
                        tiempo_actual = round(time.time() - start_time, 2)
                        writer.writerow([tiempo_actual, msg.x, msg.y, msg.z, msg.vx, msg.vy])
                        
                        telemetria_actual["tiempo"] = tiempo_actual
                        telemetria_actual["x"] = round(msg.x, 2)
                        telemetria_actual["y"] = round(msg.y, 2)
                        telemetria_actual["z"] = round(msg.z, 2)
                        telemetria_actual["vel_x"] = round(msg.vx, 2)
                        telemetria_actual["vel_y"] = round(msg.vy, 2)
                        
                        print(f"[TELEMETRY] T: {tiempo_actual}s | X: {telemetria_actual['x']} | Y: {telemetria_actual['y']} | Z: {telemetria_actual['z']}")
                        
            break 
        except PermissionError:
            print(f"[ERROR] Permiso denegado al escribir en {ARCHIVO_LOG}. Reintentando...")
            time.sleep(3)

# --- EXTRACCIÓN DE DATOS LIDAR (API NATIVA AIRSIM) ---
def extraer_lidar():
    global grabando_telemetria
    print("[LIDAR] Iniciando hilo puente con la API de AirSim (Port 41451)...")
    try:
        # Conexión directa a Windows desde el contenedor Docker
        client_airsim = airsim.MultirotorClient(ip='host.docker.internal')
        client_airsim.confirmConnection()
        print("[LIDAR] API conectada correctamente. Escuchando Nube de Puntos...")
        
        while grabando_telemetria:
            lidar_data = client_airsim.getLidarData(lidar_name="Lidar1", vehicle_name="PX4")
            
            # Point cloud returns an array of floats (X, Y, Z for each point)
            if len(lidar_data.point_cloud) >= 3:
                num_puntos = int(len(lidar_data.point_cloud) / 3)
                print(f"[LIDAR-SENSOR] Point Cloud recibida | Densidad: {num_puntos} puntos")
            
            # Consultamos los datos a baja frecuencia (1 Hz) para no asfixiar la consola
            time.sleep(1.0)
            
    except Exception as e:
        print(f"[ERROR LIDAR] No se pudo conectar o leer datos de AirSim: {e}")

# --- NAVEGACIÓN BASADA EN WAYPOINTS ---
def navegar_a_punto(target_x, target_y, target_z, tolerancia=4.0):
    print(f"[NAV] Asignando nuevo setpoint -> X:{target_x}, Y:{target_y}, Z:{target_z}")
    target_actual["x"] = float(target_x)
    target_actual["y"] = float(target_y)
    target_actual["z"] = float(target_z)
    
    while grabando_telemetria:
        dist_x = target_actual["x"] - telemetria_actual["x"]
        dist_y = target_actual["y"] - telemetria_actual["y"]
        dist_z = target_actual["z"] - telemetria_actual["z"]
        distancia = math.sqrt(dist_x**2 + dist_y**2 + dist_z**2)
        
        if distancia <= tolerancia:
            print("[NAV] Waypoint alcanzado satisfactoriamente.")
            break
            
        time.sleep(0.1)

# --- RUTINA PRINCIPAL DE VUELO ---
def ejecutar_vuelo():
    global grabando_telemetria
    time.sleep(2) 
    
    try:
        target_actual["x"] = 0.0
        target_actual["y"] = 0.0
        target_actual["z"] = 0.0
        
        print("[SYSTEM] Estabilizando parámetros de control iniciales...")
        time.sleep(2)

        print("[FLIGHT_CTRL] Solicitando modo de vuelo: OFFBOARD (PX4)")
        # Transmisión directa de comando MAV_CMD_DO_SET_MODE para modo OFFBOARD
        master.mav.command_long_send(master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_DO_SET_MODE, 0, 209.0, 6.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        time.sleep(1)

        print("[FLIGHT_CTRL] Enviando comando de armado (ARM_DISARM)...")
        armado = False
        while not armado:
            master.mav.command_long_send(
                master.target_system, master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
            )
            print("[MAVLINK] Esperando confirmación de armado vía telemetría...")
            
            # Esperamos 5 segundos el mensaje de armado. Si no llega, reintentamos (por si el EKF aún no converge)
            msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=5.0)
            if msg and (msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED):
                armado = True
                print("[FLIGHT_CTRL] Confirmación recibida. Motores armados exitosamente.")
            else:
                print("[FLIGHT_CTRL] Armado rechazado (posible EKF sin converger). Reintentando en 5s...")
                time.sleep(1)

        print(f"[NAV] Ejecutando despegue autónomo hacia altitud: {abs(ALTURA_SEGURA)}m")
        target_actual["z"] = ALTURA_SEGURA
        
        # Secuencia de espera para alcanzar la altitud de despegue
        navegar_a_punto(0, 0, ALTURA_SEGURA, tolerancia=2.0)

        # Matriz de ruta planificada para mapeo
        puntos_ruta = [
            (200.0, 0.0, ALTURA_SEGURA), (200.0, 200.0, ALTURA_SEGURA),
            (0.0, 200.0, ALTURA_SEGURA), (-200.0, 200.0, ALTURA_SEGURA),
            (-200.0, 0.0, ALTURA_SEGURA), (-200.0, -200.0, ALTURA_SEGURA),
            (0.0, -200.0, ALTURA_SEGURA), (200.0, -200.0, ALTURA_SEGURA),
            (200.0, 0.0, ALTURA_SEGURA), (0.0, 0.0, ALTURA_SEGURA)
        ]

        print("[NAV] Altitud de seguridad alcanzada. Iniciando ruta de mapeo.")
        for punto in puntos_ruta:
            navegar_a_punto(punto[0], punto[1], punto[2])

        print("[FLIGHT_CTRL] Misión completada. Iniciando secuencia de aterrizaje.")
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND, 
            0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        )

        print("[NAV] Descenso en progreso...")
        while telemetria_actual["z"] < -1.0:
            time.sleep(0.5)
            
        print("[FLIGHT_CTRL] Vehículo en tierra. Esperando desarmado automático.")
        time.sleep(3)

        grabando_telemetria = False
        print("[SYSTEM] Rutina de vuelo finalizada correctamente.")
        
    except Exception as e:
        print(f"[ERROR] Excepción detectada durante la secuencia de vuelo: {e}")
        traceback.print_exc()
        grabando_telemetria = False 

def activar_failsafe_rtl():
    print("\n[SYSTEM][EMERGENCIA] Interrupción manual detectada (Ctrl+C).")
    print("[SYSTEM][EMERGENCIA] Abortando misión y enviando comando RTL (Return To Launch)...")
    try:
        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_RETURN_TO_LAUNCH, 0, 
            0, 0, 0, 0, 0, 0, 0
        )
        print("[SYSTEM][EMERGENCIA] Comando RTL enviado al vehículo.")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar el comando RTL: {e}")

# ==============================================================
# BLOQUE PRINCIPAL (ENTRY POINT)
# ==============================================================
if __name__ == '__main__':
    def signal_handler(sig, frame):
        global grabando_telemetria
        grabando_telemetria = False
        activar_failsafe_rtl()
        print("[SYSTEM] Estación terrena apagada. El dron continuará en RTL.")
        sys.exit(0)

    # Registrar el manejador de señales para capturar Ctrl+C sin que Flask lo bloquee
    signal.signal(signal.SIGINT, signal_handler)

    print("[SYSTEM] Iniciando servicios en segundo plano...")
    threading.Thread(target=registrar_datos, daemon=True).start()
    threading.Thread(target=ejecutar_vuelo, daemon=True).start()
    threading.Thread(target=extraer_lidar, daemon=True).start()
    
    # Asignación de puerto estático para evitar colisiones
    puerto_actual = 5001
    while puerto_actual < 5020: 
        try:
            print("-" * 60)
            print(f"[GCS] Estación Terrena activa en: http://127.0.0.1:{puerto_actual}")
            print("-" * 60)
            
            # Intentar abrir el navegador automáticamente (compatible con WSL/Windows)
            import os, subprocess
            url = f"http://127.0.0.1:{puerto_actual}"
            try:
                if os.name == 'nt':
                    import webbrowser
                    webbrowser.open(url)
                else:
                    subprocess.Popen(["/mnt/c/Windows/System32/cmd.exe", "/c", "start", url], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                print(f"[WARNING] No se pudo abrir el navegador automáticamente: {e}")
                
            app.run(host='0.0.0.0', port=puerto_actual, use_reloader=False)
            break
        except OSError:
            puerto_actual += 1
