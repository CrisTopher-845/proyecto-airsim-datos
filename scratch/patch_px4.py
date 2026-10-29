import re

path = '/home/usuario/PX4-Autopilot/src/modules/simulation/simulator_mavlink/SimulatorMavlink.cpp'

with open(path, 'r') as f:
    content = f.read()

# Comment out the error line
content = re.sub(
    r'PX4_ERR\("poll timeout %d, %d", pret, errno\);',
    r'//PX4_ERR("poll timeout %d, %d", pret, errno);',
    content
)

with open(path, 'w') as f:
    f.write(content)
print("Done patching.")
