import airsim
import time
import csv
import threading
import logging
import math
from flask import Flask, render_template, jsonify

# Desactivar logs internos redundantes de Flask
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# --- CONFIGURACIÓN DE VUELO SEGURO ---
ALTURA_SEGURA = -100  # Altura de 100 metros
VELOCIDAD = 10        # Velocidad en m/s
ARCHIVO_LOG = "mision_mapeo_final.csv"

grabando_telemetria = True
telemetria_actual = { "tiempo": 0, "x": 0.0, "y": 0.0, "z": 0.0, "vel_x": 0.0, "vel_y": 0.0 }

# --- RUTAS WEB (API DE FLASK) ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/datos')
def obtener_datos():
    return jsonify(telemetria_actual)

# --- 1. MONITOR DE TELEMETRÍA ---
def registrar_datos():
    global grabando_telemetria, telemetria_actual
    print("[Telemetría] Canal de datos secundario activo.")
    
    cliente_telemetria = airsim.MultirotorClient()
    cliente_telemetria.confirmConnection()
    start_time = time.time()
    
    with open(ARCHIVO_LOG, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Tiempo(s)", "X", "Y", "Z", "Vel_X", "Vel_Y"])
        
        while grabando_telemetria:
            estado = cliente_telemetria.getMultirotorState()
            pos = estado.kinematics_estimated.position
            vel = estado.kinematics_estimated.linear_velocity
            tiempo_actual = round(time.time() - start_time, 2)
            
            writer.writerow([tiempo_actual, pos.x_val, pos.y_val, pos.z_val, vel.x_val, vel.y_val])
            
            telemetria_actual["tiempo"] = tiempo_actual
            telemetria_actual["x"] = round(pos.x_val, 2)
            telemetria_actual["y"] = round(pos.y_val, 2)
            telemetria_actual["z"] = round(pos.z_val, 2)
            telemetria_actual["vel_x"] = round(vel.x_val, 2)
            telemetria_actual["vel_y"] = round(vel.y_val, 2)
            
            print(f"   [En Vivo] Seg: {tiempo_actual} | X: {telemetria_actual['x']}m | Y: {telemetria_actual['y']}m | Alt Z: {telemetria_actual['z']}m | Vel X: {telemetria_actual['vel_x']} | Vel Y: {telemetria_actual['vel_y']}")
            
            time.sleep(0.5)

# --- 2. PILOTO AUTOMÁTICO ---
def ejecutar_vuelo():
    global grabando_telemetria
    
    print("\n[SERVIDOR] Estación Terrena lista en http://127.0.0.1:5000")
    time.sleep(3) 
    
    client = airsim.MultirotorClient()
    client.confirmConnection()
    client.enableApiControl(True)
    client.armDisarm(True)

    VELOCIDAD_ASCENSO = 15  # Ascenso rápido
    print(f"\n[DRON] Despegando y ascendiendo a {abs(ALTURA_SEGURA)} metros...")
    client.takeoffAsync().join() 
    client.moveToPositionAsync(0, 0, ALTURA_SEGURA, VELOCIDAD_ASCENSO).join()

    client.simSetWind(airsim.Vector3r(5, 3, 0))

    puntos_ruta = [
        (100, 0, ALTURA_SEGURA, VELOCIDAD),
        (50, 75, ALTURA_SEGURA, VELOCIDAD),
        (-75, 75, ALTURA_SEGURA, VELOCIDAD),
        (-75, -75, ALTURA_SEGURA, VELOCIDAD),
        (50, -75, ALTURA_SEGURA, VELOCIDAD),
        (100, 0, ALTURA_SEGURA, VELOCIDAD),
        (0, 0, ALTURA_SEGURA, VELOCIDAD)
    ]

    for i, punto in enumerate(puntos_ruta):
        client.moveToPositionAsync(punto[0], punto[1], punto[2], punto[3]).join()

    client.simSetWind(airsim.Vector3r(0, 0, 0))
    client.landAsync().join()
    client.armDisarm(False)
    client.enableApiControl(False)

    grabando_telemetria = False
    print(f"\n--- Operación finalizada ---")

if __name__ == '__main__':
    threading.Thread(target=registrar_datos, daemon=True).start()
    threading.Thread(target=ejecutar_vuelo, daemon=True).start()
    app.run(port=5000)
    