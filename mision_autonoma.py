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
ALTURA_SEGURA = -80  
VELOCIDAD = 10        # Aumentamos a 10 m/s (36 km/h) para abarcar el gran perímetro
ARCHIVO_LOG = "mision_mapeo_final.csv"

grabando_telemetria = True
telemetria_actual = { "tiempo": 0, "z": 0.0, "vel_x": 0.0, "vel_y": 0.0 }

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
            
            # Guardamos los datos oficiales en el CSV para tu equipo
            writer.writerow([tiempo_actual, pos.x_val, pos.y_val, pos.z_val, vel.x_val, vel.y_val])
            
            # Actualizamos la memoria para el Dashboard Web
            telemetria_actual["tiempo"] = tiempo_actual
            telemetria_actual["z"] = round(pos.z_val, 2)
            telemetria_actual["vel_x"] = round(vel.x_val, 2)
            telemetria_actual["vel_y"] = round(vel.y_val, 2)
            
            # Imprimimos en consola
            print(f"   [En Vivo] Seg: {tiempo_actual} | Alt Z: {telemetria_actual['z']}m | Vel X: {telemetria_actual['vel_x']} | Vel Y: {telemetria_actual['vel_y']}")
            time.sleep(0.5)

# --- 2. PILOTO AUTOMÁTICO (COMUNICACIÓN ININTERRUMPIDA) ---
def ejecutar_vuelo():
    global grabando_telemetria
    
    print("\n[SERVIDOR] Estación Terrena lista en http://127.0.0.1:5000")
    time.sleep(3) 
    
    client = airsim.MultirotorClient()
    client.confirmConnection()
    client.enableApiControl(True)
    client.armDisarm(True)

    VELOCIDAD_ASCENSO = 5  
    print(f"\n[DRON] Despegando y ascendiendo a {abs(ALTURA_SEGURA)} metros...")
    client.takeoffAsync().join() 
    client.moveToPositionAsync(0, 0, ALTURA_SEGURA, VELOCIDAD_ASCENSO).join()

    # Viento activado.
    print("\n[!] Inyectando viento cruzado (5m/s X, 3m/s Y) de forma continua...")
    client.simSetWind(airsim.Vector3r(5, 3, 0))

    # --- NUEVA RUTA: Hexágono Extendido ---
    puntos_ruta = [
        (200, 0, ALTURA_SEGURA, VELOCIDAD),     # WP1: Extremo Norte
        (100, 150, ALTURA_SEGURA, VELOCIDAD),   # WP2: Noreste diagonal
        (-150, 150, ALTURA_SEGURA, VELOCIDAD),  # WP3: Sureste largo
        (-150, -150, ALTURA_SEGURA, VELOCIDAD), # WP4: Suroeste cruzando
        (100, -150, ALTURA_SEGURA, VELOCIDAD),  # WP5: Noroeste diagonal
        (200, 0, ALTURA_SEGURA, VELOCIDAD),     # WP6: Cierra el hexágono en el Norte
        (0, 0, ALTURA_SEGURA, VELOCIDAD)        # WP7: Aterrizaje en el centro
    ]

    print(f"\n[DRON] Iniciando Circuito Hexagonal Extendido. ({len(puntos_ruta)} Waypoints)...")
    for i, punto in enumerate(puntos_ruta):
        print(f"-> Navegando al WP {i+1}/{len(puntos_ruta)} | Destino X: {punto[0]} | Y: {punto[1]}")
        client.moveToPositionAsync(punto[0], punto[1], punto[2], punto[3]).join()

    print("\n[DRON] Ruta completada. Estabilizando para el descenso...")
    client.simSetWind(airsim.Vector3r(0, 0, 0))
    client.moveToPositionAsync(0, 0, ALTURA_SEGURA, VELOCIDAD_ASCENSO).join()
    client.landAsync().join()
    client.armDisarm(False)
    client.enableApiControl(False)

    grabando_telemetria = False
    print(f"\n--- Operación finalizada. Log guardado en {ARCHIVO_LOG} ---")

# --- 3. INICIALIZACIÓN ---
if __name__ == '__main__':
    threading.Thread(target=registrar_datos, daemon=True).start()
    threading.Thread(target=ejecutar_vuelo, daemon=True).start()
    app.run(port=5000)

   #1  
   #2
#hola 