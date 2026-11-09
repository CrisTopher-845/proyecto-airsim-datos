import airsim
import time
import sys
import os
import numpy as np

print("Conectando al simulador AirSim...")
client = airsim.MultirotorClient()
client.confirmConnection()

output_dir = "dataset_lidar"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print(f"Iniciando captura continua. Los archivos se guardarán en la carpeta '{output_dir}'.")
print("Presiona Ctrl+C para detener la grabación.")

frame_count = 0
try:
    while True:
        lidar_data = client.getLidarData(lidar_name="Lidar1", vehicle_name="PX4")
        
        if len(lidar_data.point_cloud) < 3:
            print("No se detectaron puntos en este fotograma.")
            time.sleep(0.1)
            continue
            
        points = np.array(lidar_data.point_cloud, dtype=np.float32)
        points = np.reshape(points, (int(points.shape[0]/3), 3))
        
        filename = os.path.join(output_dir, f"frame_{frame_count:04d}.ply")
        with open(filename, 'w') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {points.shape[0]}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")
            for p in points:
                f.write(f"{p[0]} {p[1]} {p[2]}\n")
                
        print(f"[{frame_count:04d}] Guardados {points.shape[0]} puntos en {filename}")
        frame_count += 1
        time.sleep(0.1) # Captura a 10 FPS para no saturar el disco duro
except KeyboardInterrupt:
    print("\nGrabación detenida por el usuario. Dataset guardado.")
