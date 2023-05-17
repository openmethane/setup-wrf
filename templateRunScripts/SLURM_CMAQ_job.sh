#!/bin/bash

## run name
#SBATCH -J TEMPLATE

## wall time
#SBATCH -t 10:00:00

## memory
# Use --mem-per-cpu or --mem depending on whether SelectType is
# set to select/cons_res or select/linear. See the sbatch man pages.
#SBATCH --mem-per-cpu=8192

## number of nodes
#SBATCH -N 1

## processors per node
#SBATCH --ntasks-per-node=40

## where the output from SLURM should be directed
#SBATCH -o TEMPLATE

# Load CMAQ environment variables
source TEMPLATE

# Call the main run script and redirect output to file
TEMPLATE >& TEMPLATE

# Cleanup


