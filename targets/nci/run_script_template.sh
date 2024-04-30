#!/bin/bash

#PBS -N ${RUNSHORT}_${STARTDATE}
#PBS -l walltime=12:00:00
#PBS -l mem=128GB
#PBS -l ncpus=32
#PBS -j oe
#PBS -q normal
#PBS -l wd
#PBS -P q90
#PBS -l storage=gdata/sx70+gdata/hh5+gdata/ua8+gdata/ub4

module purge
module load dot
module load pbs
module load intel-compiler/2019.3.199
module load openmpi/4.0.2
module load hdf5/1.10.5
module load netcdf/4.7.1
module load nco
module use /g/data3/hh5/public/modules
module load conda/analysis3

ulimit -s unlimited
cd ${RUN_DIR}

python3 checkWrfoutInBackground.py &
backgroundPID=$!

echo running with $PBS_NCPUS mpi ranks
time /apps/openmpi/4.0.2/bin/mpirun -np $PBS_NCPUS -report-bindings ./wrf.exe >& wrf.log

## give the python script a chance to finish
sleep 75

## kill the process that was running in the background
kill $backgroundPID

if [ ! -e rsl.out.0000 ] ; then
    echo "wrf.exe did not complete successfully - exiting"
    exit
fi

issuccess=`grep -c "SUCCESS COMPLETE WRF" rsl.out.0000`
echo $issuccess

if [ "$issuccess" -eq 0 ] ; then
    echo "wrf.exe did not complete successfully - exiting"
    exit
fi

# We don't need the linked restart files any more
find . -name 'wrfrst*' -type f -delete

if [ "$issuccess" -gt 0 ] ; then
   echo "cleaning up now"
   qsub cleanup.sh
fi
