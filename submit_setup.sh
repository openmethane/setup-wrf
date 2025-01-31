#!/bin/bash
#PBS -N setupWRF
#PBS -l walltime=10:00:00
#PBS -l mem=16GB
#PBS -l ncpus=1
#PBS -j oe
#PBS -q copyq
#PBS -l wd
#PBS -l storage=gdata/sx70+gdata/hh5+gdata/ua8+gdata/ub4
#PBS -P q90

source load_conda_env.sh

python scripts/setup_for_wrf.py -c config/config.nci.json

