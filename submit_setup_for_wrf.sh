#!/bin/bash

#PBS -P q90
#PBS -q copyq
#PBS -N setup_for_wrf
#PBS -l walltime=10:00:00,mem=96GB
#PBS -l storage=scratch/lp86+gdata/hh5+gdata/lp86+gdata/sx70
#PBS -l ncpus=1
#PBS -l wd
###PBS -j oe

source /home/563/pjr563/openmethane-beta/setup-wrf/load_conda_env.sh

python3 setup_for_wrf.py
