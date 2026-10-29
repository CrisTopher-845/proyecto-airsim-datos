import re

world_path = 'gazebo_cave_world/worlds/cave_world.world'
out_path = 'gazebo_cave_world/worlds/cave_world_fast.world'

with open(world_path, 'r') as f:
    content = f.read()

# Completely remove all <collision> blocks, ensuring we don't leave empty tags
# We use regex to find <collision> tags and their contents up to </collision>
# and replace them with nothing.
content = re.sub(r'<collision[^>]*>[\s\S]*?</collision>', '', content)

with open(out_path, 'w') as f:
    f.write(content)

print(f"Created {out_path} completely without collisions.")
