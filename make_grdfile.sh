#!/bin/sh
# script for makeing CMAQ grid file from GRIDDESC
# wrapper for the latlon program
# copyright the SuperPower Institute 2023
module purge
module load pbs dot nco 
module use /g/data3/hh5/public/modules/ 
module load conda/analysis3
export GRIDDESC="/home/563/pjr563/scratch/openmethane-beta/mcip/2022-07-01/d01/GRIDDESC"
export GRDFILE="/home/563/pjr563/scratch/openmethane-beta/mcip/2022-07-01/d01/GRDFILE.nc"
export BDYFILE="/home/563/pjr563/scratch/openmethane-beta/mcip/2022-07-01/d01/GRIDBDY2D_1"
/home/563/sa6589/Linux2_x86_64/latlon
