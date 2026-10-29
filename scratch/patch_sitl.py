import os

file_path = '/home/usuario/PX4-Autopilot/Tools/simulation/gazebo-classic/sitl_run.sh'
with open(file_path, 'r') as f:
    content = f.read()

target = '-x 1.01 -y 0.98 -z 0.83'
replacement = '-x ${PX4_SITL_X:-1.01} -y ${PX4_SITL_Y:-0.98} -z ${PX4_SITL_Z:-0.83}'

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Patched sitl_run.sh successfully!")
else:
    print("Target string not found in sitl_run.sh (already patched?)")
