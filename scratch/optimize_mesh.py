import os
import numpy as np

base_dir = '/mnt/c/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/gazebo_cave_world/worlds/models/cave_world'
obj_in = os.path.join(base_dir, 'meshes/cave_world.obj')
obj_out = os.path.join(base_dir, 'meshes/cave_world_collision.obj')
sdf_path = os.path.join(base_dir, 'model.sdf')

print("[1/3] Cargando malla original de la cueva...")
verts = []
faces = []
with open(obj_in, 'r') as f:
    for line in f:
        if line.startswith('v '):
            parts = line.split()
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
        elif line.startswith('f '):
            parts = line.split()[1:]
            f_idx = [int(p.split('/')[0]) - 1 for p in parts]
            if len(f_idx) == 3:
                faces.append(f_idx)

verts = np.array(verts, dtype=np.float32)
faces = np.array(faces, dtype=np.int32)
print(f"Original: {len(verts)} vertices, {len(faces)} caras.")

print("[2/3] Aplicando simplificación por Voxel Grid (0.75m)...")
voxel_size = 0.75
v_grid = np.floor(verts / voxel_size).astype(np.int64)
unique_cells, inverse = np.unique(v_grid, axis=0, return_inverse=True)

# Centroide por celda
new_verts = np.zeros((len(unique_cells), 3), dtype=np.float32)
counts = np.zeros(len(unique_cells), dtype=np.int32)
np.add.at(new_verts, inverse, verts)
np.add.at(counts, inverse, 1)
new_verts /= counts[:, None]

mapped_faces = inverse[faces]
valid = (mapped_faces[:, 0] != mapped_faces[:, 1]) & \
        (mapped_faces[:, 1] != mapped_faces[:, 2]) & \
        (mapped_faces[:, 0] != mapped_faces[:, 2])
clean_faces = mapped_faces[valid]

sorted_faces = np.sort(clean_faces, axis=1)
_, unique_face_indices = np.unique(sorted_faces, axis=0, return_index=True)
final_faces = clean_faces[unique_face_indices]

print(f"Simplificado para colisiones: {len(new_verts)} vertices, {len(final_faces)} caras (reducción del {100 - (len(final_faces)/len(faces)*100):.1f}%).")

print("[3/3] Guardando cave_world_collision.obj...")
with open(obj_out, 'w') as f:
    f.write("# Optimized collision mesh for Gazebo ODE\n")
    for v in new_verts:
        f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
    for face in final_faces:
        f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

print("Actualizando model.sdf de cave_world...")
with open(sdf_path, 'r') as f:
    sdf_content = f.read()

sdf_content = sdf_content.replace(
    'model://cave_world/meshes/cave_world.obj</uri>\n          </mesh>\n        </geometry>\n      </collision>',
    'model://cave_world/meshes/cave_world_collision.obj</uri>\n          </mesh>\n        </geometry>\n      </collision>'
)

with open(sdf_path, 'w') as f:
    f.write(sdf_content)

print("¡Colisión optimizada inyectada exitosamente en cave_world!")
