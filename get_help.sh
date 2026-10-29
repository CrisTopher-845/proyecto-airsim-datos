#!/bin/bash
export PATH=$PATH:$HOME/.local/bin:$HOME/ardupilot/Tools/autotest
sim_vehicle.py -h > help_sim.txt
arducopter -h > help_ardu.txt
