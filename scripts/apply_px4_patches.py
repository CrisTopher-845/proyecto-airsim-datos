#!/usr/bin/env python3
import os
import re
import sys

def patch_file(filepath, search_str, replace_str, description):
    if not os.path.exists(filepath):
        print(f"[-] Saltando {description} (archivo no encontrado: {filepath})")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if replace_str in content:
        print(f"[+] {description}: Ya aplicado previamente.")
        return True

    if search_str in content:
        content = content.replace(search_str, replace_str)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[✓] {description}: Parche aplicado con éxito.")
        return True
    else:
        print(f"[!] {description}: Cadena original no encontrada (puede que ya esté modificada o la versión sea distinta).")
        return False

def patch_regex(filepath, pattern, replacement, description):
    if not os.path.exists(filepath):
        print(f"[-] Saltando {description} (archivo no encontrado: {filepath})")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[✓] {description}: Parche regex aplicado con éxito.")
        return True
    else:
        print(f"[+] {description}: Ya actualizado o patrón no requerido.")
        return False

def main():
    px4_dir = os.environ.get("PX4_DIR", os.path.expanduser("~/PX4-Autopilot"))
    print(f"=== Aplicando parches del proyecto a PX4-Autopilot en: {px4_dir} ===")

    # 1. Parche de spawn dinámico en sitl_run.sh
    sitl_run = os.path.join(px4_dir, "Tools/simulation/gazebo-classic/sitl_run.sh")
    patch_file(
        sitl_run,
        "-x 1.01 -y 0.98 -z 0.83",
        "-x ${PX4_SITL_X:-1.01} -y ${PX4_SITL_Y:-0.98} -z ${PX4_SITL_Z:-0.83}",
        "Spawn configurable (PX4_SITL_X/Y/Z) en sitl_run.sh"
    )

    # 2. Silenciar spam de poll timeout en SimulatorMavlink.cpp
    sim_mavlink = os.path.join(px4_dir, "src/modules/simulation/simulator_mavlink/SimulatorMavlink.cpp")
    patch_regex(
        sim_mavlink,
        r'(?<!//)PX4_ERR\("poll timeout %d, %d", pret, errno\);',
        r'//PX4_ERR("poll timeout %d, %d", pret, errno);',
        "Silenciar poll timeout en SimulatorMavlink.cpp"
    )

    # 3. Comentar px4-rc.mavlink en rcS si existe
    rcs_file = os.path.join(px4_dir, "ROMFS/px4fmu_common/init.d-posix/rcS")
    patch_regex(
        rcs_file,
        r'^\. px4-rc\.mavlink',
        r'# . px4-rc.mavlink',
        "Desactivar . px4-rc.mavlink en rcS"
    )

    # 4. Actualizar sensor RPLIDAR si existe
    rplidar_file = os.path.join(px4_dir, "Tools/simulation/gazebo-classic/sitl_gazebo-classic/models/rplidar/model.sdf")
    if os.path.exists(rplidar_file):
        with open(rplidar_file, 'r', encoding='utf-8') as f:
            rplidar_content = f.read()
        
        # Si contiene el plugin antiguo libgazebo_ros_laser.so, sugerir o reemplazar
        if "libgazebo_ros_laser.so" in rplidar_content and "libgazebo_ros_ray_sensor.so" not in rplidar_content:
            old_plugin = """        <plugin name="gazebo_ros_head_rplidar_controller" filename="libgazebo_ros_laser.so">
          <topicName>laser/scan</topicName>
          <frameName>rplidar_link</frameName>
        </plugin>"""
            new_plugin = """        <plugin name="gazebo_ros_rplidar" filename="libgazebo_ros_ray_sensor.so">
          <ros>
            <remapping>~/out:=scan</remapping>
          </ros>
          <output_type>sensor_msgs/LaserScan</output_type>
          <frame_name>rplidar_link</frame_name>
        </plugin>"""
            if old_plugin in rplidar_content:
                rplidar_content = rplidar_content.replace(old_plugin, new_plugin)
                with open(rplidar_file, 'w', encoding='utf-8') as f:
                    f.write(rplidar_content)
                print("[✓] Modelo rplidar actualizado a libgazebo_ros_ray_sensor.so.")

    print("=== Parches aplicados correctamente ===")

if __name__ == '__main__':
    main()

