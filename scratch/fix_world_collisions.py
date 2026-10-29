import re

world_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/gazebo_cave_world/worlds/cave_world.world'

with open(world_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix duplicate collision in tunnel_entrance
tunnel_collision = """      <link name='link'>
        <collision name='collision'>
          <geometry>
            <mesh>
              <scale>0.01 0.01 0.01</scale>
              <uri>model://tunnel_entrance/meshes/Entrance.obj</uri>
            </mesh>
          </geometry>
          <max_contacts>10</max_contacts>
          <surface>
            <contact>
              <ode/>
            </contact>
            <bounce/>
            <friction>
              <torsional>
                <ode/>
              </torsional>
              <ode/>
            </friction>
          </surface>
        </collision>
        <visual name='visual'>"""

content = re.sub(
    r"<model name='tunnel_entrance'>\s*<static>1</static>\s*<link name='link'>\s*<collision name='collision'>.*?</collision>\s*<collision name='collision'>.*?</collision>\s*<visual name='visual'>",
    "<model name='tunnel_entrance'>\n      <static>1</static>\n" + tunnel_collision,
    content,
    flags=re.DOTALL
)

# 2. Fix duplicate collision in cave_world and point collision to cave_world_collision.obj
cave_collision = """      <link name='link'>
        <pose frame=''>0 0 0 1.5708 -0 0</pose>
        <collision name='collision'>
          <geometry>
            <mesh>
              <uri>model://cave_world/meshes/cave_world_collision.obj</uri>
            </mesh>
          </geometry>
          <max_contacts>10</max_contacts>
          <surface>
            <contact>
              <ode/>
            </contact>
            <bounce/>
            <friction>
              <torsional>
                <ode/>
              </torsional>
              <ode/>
            </friction>
          </surface>
        </collision>
        <visual name='visual'>"""

content = re.sub(
    r"<model name='cave_world'>\s*<static>1</static>\s*<link name='link'>\s*<pose frame=''>0 0 0 1\.5708 -0 0</pose>\s*<collision name='collision'>.*?</collision>\s*<collision name='collision'>.*?</collision>\s*<visual name='visual'>",
    "<model name='cave_world'>\n      <static>1</static>\n" + cave_collision,
    content,
    flags=re.DOTALL
)

with open(world_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("cave_world.world updated: removed duplicate collision tags and linked cave_world_collision.obj!")
