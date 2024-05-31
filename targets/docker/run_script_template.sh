#!/bin/bash

export PBS_NCPUS=1

ulimit -s unlimited
cd ${RUN_DIR}

python3 checkWrfoutInBackground.py > wrf-background.log 2>&1 &
backgroundPID=$!

echo running with $PBS_NCPUS mpi ranks
time mpirun -np $PBS_NCPUS ./wrf.exe >& wrf.log

## give the python script a chance to finish
sleep 30

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
   ./cleanup.sh
fi
