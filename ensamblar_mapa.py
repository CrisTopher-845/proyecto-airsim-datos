import open3d as o3d
import glob

print("Buscando archivos .ply en dataset_lidar/ ...")
archivos = sorted(glob.glob('dataset_lidar/frame_*.ply'))
if not archivos:
    print("Error: No se encontraron archivos en la carpeta dataset_lidar/")
    exit()

print(f"Se encontraron {len(archivos)} fotogramas. Iniciando ensamblaje directo...")

# En AirSim, por defecto, getLidarData devuelve las coordenadas en el 
# Sistema Inercial del Vehículo (Mundo Global NED). 
# Por lo tanto, ¡no necesitamos usar algoritmos de alineación (ICP) que generen error!
# Simplemente concatenamos las nubes de puntos directamente en su posición real.

mapa_global = o3d.geometry.PointCloud()

for i, f in enumerate(archivos):
    if i % 10 == 0:
        print(f"Procesando fotograma {i}/{len(archivos)-1}...")
    
    curr_pcd = o3d.io.read_point_cloud(f)
    
    # TRUCO MÁGICO: AirSim usa coordenadas NED (Z apunta hacia abajo).
    # Esto hace que los mapas aparezcan de cabeza (como "moldes") en MeshLab o Blender.
    # Multiplicamos el eje Z por -1 para que todo apunte hacia arriba (Z-Up normal).
    import numpy as np
    puntos = np.asarray(curr_pcd.points)
    puntos[:, 2] = -puntos[:, 2]  # Invertir el eje Z
    curr_pcd.points = o3d.utility.Vector3dVector(puntos)
    
    mapa_global += curr_pcd

print("\nEnsamblaje terminado. Aplicando filtrado de suavizado para eliminar puntos duplicados...")
mapa_global = mapa_global.voxel_down_sample(voxel_size=0.1)

output_file = "mapa_global_perfecto.ply"
o3d.io.write_point_cloud(output_file, mapa_global)

print("="*50)
print(f"¡Mapa 3D global guardado exitosamente como '{output_file}'!")
print("Arrastra este nuevo archivo a CloudCompare. Verás el mapa perfecto sin distorsiones.")
print("="*50)
