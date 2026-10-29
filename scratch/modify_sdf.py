import os

template_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/custom_models/iris_with_lidar/iris_template.sdf'
output_path = 'c:/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/custom_models/iris_with_lidar/model.sdf'

with open(template_path, 'r') as f:
    content = f.read()

lidar_xml = """
    <!-- Lidar para SLAM 2D y Evasión (Cartographer) -->
    <link name="lidar_link">
      <pose>0 0 0.1 0 0 0</pose>
      <inertial>
        <mass>0.1</mass>
      </inertial>
      <visual name="lidar_visual">
        <geometry>
          <cylinder>
            <radius>0.03</radius>
            <length>0.05</length>
          </cylinder>
        </geometry>
        <material>
          <ambient>0.1 0.1 0.1 1</ambient>
        </material>
      </visual>
      <sensor name="lidar_sensor" type="ray">
        <pose>0 0 0 0 0 0</pose>
        <visualize>true</visualize>
        <update_rate>10</update_rate>
        <ray>
          <scan>
            <horizontal>
              <samples>360</samples>
              <resolution>1</resolution>
              <min_angle>-3.14159</min_angle>
              <max_angle>3.14159</max_angle>
            </horizontal>
          </scan>
          <range>
            <min>0.15</min>
            <max>10.0</max>
            <resolution>0.01</resolution>
          </range>
        </ray>
        <plugin name="gazebo_ros_lidar" filename="libgazebo_ros_ray_sensor.so">
          <ros>
            <namespace>/drone</namespace>
            <remapping>~/out:=scan</remapping>
          </ros>
          <output_type>sensor_msgs/LaserScan</output_type>
          <frame_name>lidar_link</frame_name>
        </plugin>
      </sensor>
    </link>
    <joint name="lidar_joint" type="fixed">
      <parent>base_link</parent>
      <child>lidar_link</child>
    </joint>
"""

content = content.replace("<model name='iris'>", "<model name='iris_with_lidar'>")
content = content.replace("</model>", lidar_xml + "\n  </model>")

with open(output_path, 'w') as f:
    f.write(content)

print("model.sdf updated successfully!")
