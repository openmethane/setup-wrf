#!/usr/bin/env python
from ecmwfapi import ECMWFDataServer
import datetime
from dateutil.relativedelta import relativedelta
import subprocess
import os

server = ECMWFDataServer()

## spatial range
latitudeRange = [25.0,50.0]
longitudeRange = [35.0,65.0]

## time range
dstart = datetime.datetime(2019, 2,1,0,0,0)
dend   = datetime.datetime(2019, 3,1,0,0,0)

##
prefix = "GFAS_Iran"
outfile_grib = "{}.grib".format(prefix)
outfile_nc = "{}.grib".format(prefix)
request = {
    "class": "mc",
    "dataset": "cams_gfas",
    "date": "{}/to/{}".format(dstart.date(), dend.date() ),
    "expver": "0001",
    "levtype": "sfc",
    "param": "80.210/81.210/82.210/83.210/84.210/85.210/86.210/87.210/88.210/89.210/90.210/91.210/92.210/97.210/99.210/100.210/102.210/103.210/104.210/105.210/106.210/107.210/108.210/109.210/110.210/111.210/112.210/113.210/114.210/115.210/116.210/117.210/118.210/119.210/120.210/231.210/232.210/233.210/234.210/235.210/236.210/237.210/238.210/239.210/240.210/241.210",
    "step": "0-24",
    "stream": "gfas",
    ## for area, North/West/South/East;
    "area" : "{}/{}/{}/{}".format(latitudeRange[1], longitudeRange[0],
                                  latitudeRange[0], longitudeRange[1]),
    "time": "00:00:00",
    "type": "ga",
    "target": outfile_grib,
}
##
## send request and wait for the data back
server.retrieve(request)
## convert from .grib to .nc (netCDF3)
cmds = ['ncl_convert2nc',outfile_grib]
stdout, stderr = subprocess.Popen(cmds, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()
if os.path.exists(outfile_nc):
    os.remove(outfile_grib)
else:
    print("Error in convering grib to netcdf")
## convert from netCDF3 to compressed netCDF4
cmds = ['ncks','-O','-4','-L4',outfile_nc,outfile_nc]
stdout, stderr = subprocess.Popen(cmds, stdout = subprocess.PIPE, stderr = subprocess.PIPE).communicate()
