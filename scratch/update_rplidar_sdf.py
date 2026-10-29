rplidar_sdf = """<?xml version="1.0" ?>
<sdf version="1.5">
  <model name="rplidar">
    <link name="link">

      <inertial>
        <pose>0 0 0 0 0 0</pose>
        <mass>0.19</mass>
        <inertia>
          <ixx>4.15e-6</ixx>
          <ixy>0</ixy>
          <ixz>0</ixz>
          <iyy>2.407e-6</iyy>
          <iyz>0</iyz>
          <izz>2.407e-6</izz>
        </inertia>
      </inertial>

      <visual name="visual">
        <geometry>
          <box>
            <size>0.02 0.05 0.05</size>
          </box>
        </geometry>
      </visual>

      <sensor name="laser" type="ray">
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
            <min>0.2</min>
            <max>6.0</max>
            <resolution>0.05</resolution>
          </range>
        </ray>
        <plugin name="gazebo_ros_rplidar" filename="libgazebo_ros_ray_sensor.so">
          <ros>
            <remapping>~/out:=scan</remapping>
          </ros>
          <output_type>sensor_msgs/LaserScan</output_type>
          <frame_name>rplidar_link</frame_name>
        </plugin>
        <always_on>1</always_on>
        <update_rate>10</update_rate>
        <visualize>false</visualize>
      </sensor>
    </link>
  </model>
</sdf>
"""

target = '/home/usuario/PX4-Autopilot/Tools/simulation/gazebo-classic/sitl_gazebo-classic/models/rplidar/model.sdf'
with open(target, 'w') as f:
    f.write(rplidar_sdf)

print("rplidar model.sdf updated: visualize disabled, native ROS 2 humble plugin injected!")
