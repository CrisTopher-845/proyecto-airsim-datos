import re

paths = [
    '/home/usuario/PX4-Autopilot/Tools/simulation/gazebo-classic/sitl_gazebo-classic/models/iris/iris.sdf',
    'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/custom_models/iris_with_lidar/model.sdf'
]

for path in paths:
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        content = re.sub(r'<enable_lockstep>[^<]+</enable_lockstep>', '<enable_lockstep>0</enable_lockstep>', content)
        
        with open(path, 'w') as f:
            f.write(content)
        print(f"Disabled lockstep in {path}")
    except Exception as e:
        print(f"Failed to patch {path}: {e}")
