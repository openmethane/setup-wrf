#!/bin/bash
# Submit WRF for a group of consecutive days. Wait for each job to
# finish before starting the next one.

echo Start date is ${STARTDATE}
echo Run directory is ${RUN_DIR}

[ ! -e ${RUN_DIR}/${STARTDATE}/ ] && echo "directory ${RUN_DIR}/${STARTDATE} not found - exiting" && exit 1
cd ${RUN_DIR}/${STARTDATE}/ || exit 1

chmod u+x run.sh
./run.sh

n=1

startdate=${STARTDATE}

while [ $n -lt ${njobs} ]; do

  # Get the next date
  start_date=`echo $startdate | cut -b 1-8`
  start_hour=`echo $startdate | cut -b 9-10`
  startdate=`date -u +%Y%m%d%H -d "$start_date+$start_hour hours+${nhours} hours UTC"`
 
  echo $startdate
 
  # Go into the next directory
  cd ${RUN_DIR}/$startdate/ || exit 1

  # Submit run
  ./run.sh

  let n=n+1
done

cd ${RUN_DIR}|| exit 1
