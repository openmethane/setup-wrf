
#!/bin/bash

## run name
#PBS -N TEMPLATE

#PBS -l walltime=48:00:00
#PBS -l mem=96GB
#PBS -l ncpus=24
#PBS -q normal
#PBS -P lp86
##PBS -q storage=scratch/lp86+gdata/hh5
#PBS -l storage=scratch/lp86+gdata/hh5
#PBS -l wd
#PBS -l jobfs=5GB

if [ -z "${PBS_NCPUS}" ] ; then
      echo "PBS_NCPUS is empty, setting the value to 1"
      export PBS_NCPUS=1
else
      echo "PBS_NCPUS is defined and has value ${PBS_NCPUS}"
fi

# Load CMAQ environment variables
source TEMPLATE


# Call the main run script and redirect output to file
TEMPLATE >& TEMPLATE

