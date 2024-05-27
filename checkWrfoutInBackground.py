import datetime
import netCDF4
import os
import time
import resource
import subprocess

resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))


def generate_out_filename(in_file: str):
    """
    Generate the filename of the averaged WRF output

    The WRF times in the filename are converted to ISO8601 format
    (with a trailing Z to indicate UTC time).
    These filenames play nicer with non-linux filesystems.
    """
    filename_chunks = in_file.split('_')
    time_str = '_'.join(filename_chunks[2:])

    # Convert to iso8601 format
    date = datetime.datetime.strptime(time_str, "%Y-%m-%d_%H:%M:%S")
    filename_time = date.isoformat(timespec="minutes").replace(":", "")

    out_file = f"{filename_chunks[0].upper()}_{filename_chunks[1]}_{filename_time}Z.nc"
    return out_file, time_str


while True:
    time.sleep(1)
    Files = os.listdir('.')
    Files = [File for File in Files if File.startswith('wrfout_')]
    for inFile in Files:
        mtimeAgo = time.time() - os.path.getmtime(inFile)
        ## print File, mtimeAgo
        if mtimeAgo > 10.0:
            nc = netCDF4.Dataset(inFile)
            ntimes = len(nc.dimensions['Time'])
            nc.close()
            ##
            if ntimes == 12:
                outFile, timestr = generate_out_filename(inFile)

                cmds = ['python','averageFields.py','-i',inFile,'-o',outFile,'-t',timestr]
                ## print ' '.join(cmds)
                p = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if p.returncode != 0 or len(stderr) > 0:
                    print('Error processing',inFile)
                    print('stderr:',stderr)
                    print('returncode:',p.returncode)
                elif not os.path.exists(outFile):
                    print("output file not created:",outFile)
                else:
                    ## if the process completed successfully and the output file is found, then delete the input file
                    os.remove(inFile)
