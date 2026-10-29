#!/bin/bash
unset ROS_VERSION
unset ROS_DISTRO
export ROS_LOCALHOST_ONLY=1
export LC_ALL=C
export LANG=C
export PX4_SIM_HOSTNAME=127.0.0.1
export GAZEBO_IP=127.0.0.1
export PX4_LOCKSTEP=0

cd ~/PX4-Autopilot
export HEADLESS=1
export PX4_SIMULATOR_TIMEOUT=300
export PX4_SITL_WORLD=empty
export LIBGL_ALWAYS_SOFTWARE=1

echo "[TEST] Iniciando mundo VACIO. Si esto arranca en 5 segundos, PX4 funciona."
make px4_sitl gazebo-classic_iris
