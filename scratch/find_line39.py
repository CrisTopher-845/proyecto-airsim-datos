import glob
import os
for f in glob.glob('/home/usuario/PX4-Autopilot/**/*.sh', recursive=True) + glob.glob('/home/usuario/PX4-Autopilot/**/rcS', recursive=True):
    try:
        lines = open(f).readlines()
        if len(lines) >= 39 and '[' in lines[38]:
            print(f, lines[38].strip())
    except:
        pass
