import re

paths = [
    '/home/usuario/PX4-Autopilot/Tools/simulation/gazebo-classic/sitl_gazebo-classic/models/iris/iris.sdf'
]

for path in paths:
    try:
        with open(path, 'r') as f:
            content = f.read()
        
        content = re.sub(r'<enable_lockstep>0</enable_lockstep>', '<enable_lockstep>1</enable_lockstep>', content)
        
        with open(path, 'w') as f:
            f.write(content)
        print(f"Re-enabled lockstep in {path}")
    except Exception as e:
        print(f"Failed to patch {path}: {e}")
