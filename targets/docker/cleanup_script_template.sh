#!/bin/bash

ulimit -s unlimited

cd ${RUN_DIR}

du -hc .

echo "Remove temporary files"
rm -f met_em*
rm -f geo_em*
rm -f link_grib.csh
rm -f Vtable
rm -r -f metgrid
rm -f metgrid.exe metgrid.log*
rm -f myoutfields*
rm -f namelist.output
#rm -r realrsl rsl*
rm -f wrf.log wrf.exe ungrib.exe ungrib.log real.exe real.log
rm -f FILE* GRIB* *DATA *TBL
rm -r -f ei_tmp analysis_tmp sst_tmp
rm -f SST\:*
rm -f ERA\:*
rm -f fort.*
rm -f *{DAT,formatted,CAM,asc,TBL,dat,tbl,txt,tr}*
rm -f wrfbdy* wrfinput* wrflow* nco* wrffdda* 

echo "Remove files during the spinup period "
for wrfoutfile in `find . -type f -iname 'wrfout_*'` ; do
    datetime=`basename $wrfoutfile | cut -c12-26`
    if [[ "$datetime" < "${firstTimeToKeep}" ]] ; then
	    rm -fv $wrfoutfile
    fi
done

for file in wrfout_*; do
  echo "WARNING: $file remains unprocessed"
done

echo "Compress files"
./nccopy_compress_output.sh .

du -hc .
