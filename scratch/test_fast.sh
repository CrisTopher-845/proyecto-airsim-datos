#!/bin/bash
killall -9 px4 gzserver gzclient ninja
rm -rf /tmp/px4*
cd ~/PX4-Autopilot
export HEADLESS=1
export PX4_LOCKSTEP=0
export LIBGL_ALWAYS_SOFTWARE=1
export GAZEBO_MODEL_DATABASE_URI=""
make px4_sitl gazebo-classic_iris > /mnt/c/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos/scratch/px4_test_fast.log 2>&1 &
sleep 20
killall -9 px4 gzserver gzclient ninja
