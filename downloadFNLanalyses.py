#################################################################
# This script was derived from code provided by CISL/rda.ucar.edu
# to download data from their archives
#
# Python Script to retrieve online Data files of 'ds083.3',
# This script uses the Python 'requests' module to download data.
#
# The original script suggests contacting
# rpconroy@ucar.edu (Riley Conroy) for further assistance.
#################################################################

import sys
import os
import requests
import datetime
import pytz

from urllib.request import build_opener

opener = build_opener()

def check_file_status(filepath, filesize):
    sys.stdout.write('\r')
    sys.stdout.flush()
    size = int(os.stat(filepath).st_size)
    percent_complete = (size/filesize)*100
    sys.stdout.write('%.3f %s' % (percent_complete, '% Completed'))
    sys.stdout.flush()

def downloadFNL(orcid, api_token, targetDir,times):
    """
    Download NCEP GDAS/FNL 0.25 Degree Global Tropospheric Analyses and Forecast Grids, ds083.3 | DOI: 10.5065/D65Q4T4Z

    Args:
        orcid = [string] orcid for which you have an account on rda.ucar.edu / CISL
        api_token = [string] api_token for  rda.ucar.edu / CISL
        targetDir = [string] Directory where the data should be downloaded
        times = [list of datetime.datetime objects] times to get analyses. Shoule be strictly at 00Z, 06Z, 12Z, 18Z and not before 2015-07-08

    Return:
        List of downloaded files

    """
    print('in downloadFNL')
    oldDir = os.getcwd()
    ## check that the target directory is indeed a directory
    assert os.path.exists(targetDir) and os.path.isdir(targetDir), "Target directory {} not found...".format(targetDir)
    os.chdir(targetDir)

    print('authenticate credentials')
    url = 'https://rda.ucar.edu/cgi-bin/login'
    values = {'orcid_id' : orcid, 'api_token' : api_token, 'action' : 'tokenlogin'}
    # Authenticate
    ret = requests.post(url,data=values)
    if ret.status_code != 200:
        print('Bad Authentication')
        print((ret.text))
        sys.exit()
    dspath = 'https://data.rda.ucar.edu/ds083.3/'
    downloaded_files = []

    FNLstartDate = pytz.UTC.localize(datetime.datetime(2015,7,8,0,0,0))
    
    for time in times:
        assert (time.hour % 6) == 0 and time.minute == 0 and time.second == 0, "Analysis time should be staggered at 00Z, 06Z, 12Z, 18Z intervals"
        assert time > FNLstartDate, "Analysis times should not be before 2015-07-08"
        filepath = time.strftime('%Y/%Y%m/gdas1.fnl0p25.%Y%m%d%H.f00.grib2')
        filename=dspath+filepath

        ofile = os.path.basename(filename)
        sys.stdout.write("downloading " + ofile + " ... ")
        sys.stdout.flush()
        infile = opener.open(filename)
        outfile = open(ofile, "wb")
        outfile.write(infile.read())
        #outfile.close()
        sys.stdout.write("done\n")

        downloaded_files.append(ofile)
    ##
    os.chdir(oldDir)
    return downloaded_files
