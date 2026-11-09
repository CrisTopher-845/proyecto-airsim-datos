import airsim
import time
import sys
import numpy as np

print("Conectando al simulador AirSim...")
client = airsim.MultirotorClient()
client.confirmConnection()

print("Solicitando datos del LiDAR (Livox Mid-360 Virtual)...")
# Lidar1 es el nombre que le dimos en el settings.json, PX4 es el vehiculo
lidar_data = client.getLidarData(lidar_name="Lidar1", vehicle_name="PX4")

if len(lidar_data.point_cloud) < 3:
    print("Error: No se recibieron datos. Asegúrate de que:")
    print("1. La simulación está corriendo y el dron ya despegó (o está en tierra).")
    print("2. Iniciaste el entorno de PX4.")
    sys.exit(1)

# Convertir la lista plana de floats [x,y,z, x,y,z...] a una matriz Nx3
points = np.array(lidar_data.point_cloud, dtype=np.float32)
points = np.reshape(points, (int(points.shape[0]/3), 3))

print(f"¡Éxito! Se capturaron {points.shape[0]} puntos láser en este escaneo.")

# Guardar en formato estandar PLY (Polygon File Format) para visualizarlo en 3D
filename = "escaneo_lidar.ply"
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

print(f"Nube de puntos guardada exitosamente como '{filename}'.")
print("Puedes abrir este archivo en visores 3D como MeshLab, CloudCompare, o en la web.")
