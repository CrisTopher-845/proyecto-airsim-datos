import re
import shutil

world_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/gazebo_cave_world/worlds/cave_world.world'
backup_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/gazebo_cave_world/worlds/cave_world.world.bak'

# Backup original
shutil.copy2(world_path, backup_path)

with open(world_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Disable shadows
content = re.sub(r'<shadows>1</shadows>', '<shadows>0</shadows>', content)
content = re.sub(r'<cast_shadows>1</cast_shadows>', '<cast_shadows>0</cast_shadows>', content)

# 2. Upgrade physics engine with ODE Quick Solver (10 iters) instead of slow exact solver
fast_physics = """    <physics name='default_physics' default='0' type='ode'>
      <gravity>0 0 -9.8066</gravity>
      <ode>
        <solver>
          <type>quick</type>
          <iters>10</iters>
          <sor>1.3</sor>
          <use_dynamic_moi_rescaling>0</use_dynamic_moi_rescaling>
        </solver>
        <constraints>
          <cfm>0</cfm>
          <erp>0.2</erp>
          <contact_max_correcting_vel>100</contact_max_correcting_vel>
          <contact_surface_layer>0.001</contact_surface_layer>
        </constraints>
      </ode>
      <max_step_size>0.004</max_step_size>
      <real_time_factor>1</real_time_factor>
      <real_time_update_rate>250</real_time_update_rate>
    </physics>"""

content = re.sub(r'<physics[^>]*>.*?</physics>', fast_physics, content, flags=re.DOTALL)

with open(world_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Optimized cave_world.world successfully!")
