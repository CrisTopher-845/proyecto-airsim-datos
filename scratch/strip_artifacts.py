import re

world_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/gazebo_cave_world/worlds/cave_world.world'

with open(world_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to remove backpack, extinguisher, survivor models
models_to_remove = ['backpack', 'extinguisher', 'survivor']

removed_count = 0
for model_base in models_to_remove:
    # Match <model name='backpack...'> ... </model>
    pattern = rf"<model name='{model_base}[^']*'>.*?</model>\s*"
    matches = re.findall(pattern, content, flags=re.DOTALL)
    removed_count += len(matches)
    content = re.sub(pattern, '', content, flags=re.DOTALL)

with open(world_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Removed {removed_count} decorative artifact models from cave_world.world!")
