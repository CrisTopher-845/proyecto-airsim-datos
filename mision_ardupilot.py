import time
import csv
import threading
import logging
import math
import signal
import sys
from pymavlink import mavutil
from flask import Flask, render_template, jsonify

# Configuración de logs de Flask (suprimir advertencias menores)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# --- PARÁMETROS DE VUELO Y TELEMETRÍA ---
ALTURA_SEGURA = -60.0  # Altitud de seguridad en metros (convención NED)
ARCHIVO_LOG = "mision_mapeo_ardupilot.csv"

grabando_telemetria = True
telemetria_actual = { "tiempo": 0, "x": 0.0, "y": 0.0, "z": 0.0, "vel_x": 0.0, "vel_y": 0.0 }
target_actual = { "x": 0.0, "y": 0.0, "z": 0.0, "yaw": 0.0 }

# --- CONEXIÓN MAVLINK ---
print("[MAVLINK] Estableciendo conexión TCP con ArduPilot (Puerto 5762)...")
master = mavutil.mavlink_connection('tcp:127.0.0.1:5762', source_system=254)
master.wait_heartbeat()
print(f"[MAVLINK] Conexión establecida. Target system ID: {master.target_system}")

# Solicitud de flujo de telemetría a 10 Hz
master.mav.request_data_stream_send(
    master.target_system,
    master.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL,
    10,
    1
)

# --- ENDPOINTS API LOCAL ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify(telemetria_actual)

# --- PROCESAMIENTO DE TELEMETRÍA ---
def registrar_datos():
    global grabando_telemetria, telemetria_actual
    print("[SYSTEM] Hilo de telemetría iniciado.")
    start_time = time.time()
    
    while grabando_telemetria:
        try:
            with open(ARCHIVO_LOG, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Tiempo(s)", "X", "Y", "Z", "Vel_X", "Vel_Y"])
                
                while grabando_telemetria:
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

# --- NAVEGACIÓN BASADA EN WAYPOINTS ---
def navegar_a_punto(target_x, target_y, target_z, target_yaw=None, tolerancia=2.0):
    if target_yaw is None:
        target_yaw = target_actual.get("yaw", 0.0)
    print(f"[NAV] Asignando nuevo setpoint -> X:{target_x}, Y:{target_y}, Z:{target_z}, Yaw:{target_yaw}")
    target_actual["x"] = float(target_x)
    target_actual["y"] = float(target_y)
    target_actual["z"] = float(target_z)
    target_actual["yaw"] = float(target_yaw)
    
    while grabando_telemetria:
        master.mav.set_position_target_local_ned_send(
            0, master.target_system, master.target_component,
            mavutil.mavlink.MAV_FRAME_LOCAL_NED,
            2552, # 0b100111111000 - Bit 10 (yaw) habilitado, antes estaba en 0b110111111000
            target_actual["x"], target_actual["y"], target_actual["z"],
            0, 0, 0, 0, 0, 0, target_actual["yaw"], 0
        )
        
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

        print("[FLIGHT_CTRL] Iniciando secuencia de armado...")
        print("[INFO] Es normal que tome hasta 30 segundos mientras el EKF inicializa el GPS.")
        
        while not master.motors_armed():
            print("[FLIGHT_CTRL] Solicitando modo de vuelo: GUIDED")
            master.set_mode('GUIDED')
            time.sleep(1)
            
            print("[FLIGHT_CTRL] Enviando comando de armado (ARM_DISARM)...")
            master.mav.command_long_send(
                master.target_system, master.target_component,
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 
                1, 0, 0, 0, 0, 0, 0
            )
            
            # Esperamos 3 segundos antes de volver a verificar para no saturar
            time.sleep(3)
            
            if master.motors_armed():
                print("[FLIGHT_CTRL] Confirmación recibida. Motores armados exitosamente.")
                break
            else:
                print("[WARNING] Armado rechazado (EKF o GPS inicializando). Reintentando en 3s...")

        print(f"[NAV] Ejecutando comando de despegue (TAKEOFF) hacia altitud: {abs(ALTURA_SEGURA)}m")
        target_actual["z"] = ALTURA_SEGURA 

        master.mav.command_long_send(
            master.target_system, master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 
            0, 0, 0, 0, 0, 0, abs(ALTURA_SEGURA)
        )
        
        while telemetria_actual["z"] > (ALTURA_SEGURA + 1):
            time.sleep(0.5)

        print("[NAV] Altitud de seguridad alcanzada. Iniciando ruta de mapeo 260x260m en doble cuadrícula (Overscan).")
        puntos_ruta = []
        
        area_size = 260.0
        step = 40.0
        
        inicio_x = 0.0 - (area_size / 2.0)
        inicio_y = 0.0 - (area_size / 2.0)
        
        puntos_ruta.append((inicio_x, inicio_y, ALTURA_SEGURA))
        
        y = inicio_y
        direction = 1  
        while y <= inicio_y + area_size:
            if direction == 1:
                puntos_ruta.append((inicio_x + area_size, y, ALTURA_SEGURA))
            else:
                puntos_ruta.append((inicio_x, y, ALTURA_SEGURA))
            
            y += step
            if y <= inicio_y + area_size:
                if direction == 1:
                    puntos_ruta.append((inicio_x + area_size, y, ALTURA_SEGURA))
                else:
                    puntos_ruta.append((inicio_x, y, ALTURA_SEGURA))
            
            direction *= -1

        x_start = puntos_ruta[-1][0] 
        x = x_start
        direction = 1 if x_start == inicio_x else -1
        
        while (x <= inicio_x + area_size if direction == 1 else x >= inicio_x):
            if direction == 1:
                puntos_ruta.append((x, inicio_y + area_size, ALTURA_SEGURA))
                x += step
                if x <= inicio_x + area_size:
                    puntos_ruta.append((x, inicio_y + area_size, ALTURA_SEGURA))
                    puntos_ruta.append((x, inicio_y, ALTURA_SEGURA))
                    x += step
                    if x <= inicio_x + area_size:
                        puntos_ruta.append((x, inicio_y, ALTURA_SEGURA))
            else:
                puntos_ruta.append((x, inicio_y + area_size, ALTURA_SEGURA))
                x -= step
                if x >= inicio_x:
                    puntos_ruta.append((x, inicio_y + area_size, ALTURA_SEGURA))
                    puntos_ruta.append((x, inicio_y, ALTURA_SEGURA))
                    x -= step
                    if x >= inicio_x:
                        puntos_ruta.append((x, inicio_y, ALTURA_SEGURA))

        puntos_ruta.append((0.0, 0.0, ALTURA_SEGURA))

        print("[NAV] Ruta calculada. Iniciando navegación con cámara hacia adelante.")
        pos_actual_x, pos_actual_y = 0.0, 0.0
        
        for punto in puntos_ruta:
            target_x, target_y, target_z = punto[0], punto[1], punto[2]
            
            dy = target_y - pos_actual_y
            dx = target_x - pos_actual_x
            yaw_objetivo = math.atan2(dy, dx)
            
            if math.hypot(dx, dy) > 0.5:
                target_yaw = yaw_objetivo
            else:
                target_yaw = None
                
            navegar_a_punto(target_x, target_y, target_z, target_yaw=target_yaw)
            pos_actual_x, pos_actual_y = target_x, target_y
            
        print("[NAV] Retornando al punto de origen con precisión centimétrica.")
        navegar_a_punto(0.0, 0.0, ALTURA_SEGURA, target_yaw=0.0, tolerancia=0.5)

        print("[NAV] Estabilizando inercia sobre (0,0) antes de aterrizar...")
        time.sleep(4)

        print("[FLIGHT_CTRL] Misión completada. Solicitando modo de vuelo: LAND")
        master.set_mode('LAND')

        print("[NAV] Descenso en progreso...")
        while telemetria_actual["z"] < -0.5:
            time.sleep(0.5)
            
        print("[FLIGHT_CTRL] Vehículo en tierra. Esperando desarmado automático.")
        time.sleep(3)

        grabando_telemetria = False
        print("[SYSTEM] Rutina de vuelo finalizada correctamente.")
        
    except Exception as e:
        print(f"[ERROR] Excepción detectada durante la secuencia de vuelo: {e}")
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
    
    puerto_actual = 5000
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
                
            app.run(port=puerto_actual, use_reloader=False)
            break
        except OSError:
            puerto_actual += 1
