import re

file_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/gazebo_cave_world/worlds/cave_world.world'

with open(file_path, 'r') as f:
    content = f.read()

# Remove the <state> block
content = re.sub(r'<state world_name=\'default\'>.*?</state>', '', content, flags=re.DOTALL)

# Update physics block
content = re.sub(r'<max_step_size>.*?</max_step_size>', '<max_step_size>0.004</max_step_size>', content)
content = re.sub(r'<real_time_update_rate>.*?</real_time_update_rate>', '<real_time_update_rate>250</real_time_update_rate>', content)

with open(file_path, 'w') as f:
    f.write(content)

print("cave_world.world cleaned and updated!")
