import netCDF4
import os
import time
import resource
import subprocess

resource.setrlimit(resource.RLIMIT_STACK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))

while True:
    time.sleep(1)
    Files = os.listdir('.')
    Files = [File for File in Files if File.startswith('wrfout_')]
    for inFile in Files:
        mtimeAgo = time.time() - os.path.getmtime(inFile)
        ## print File, mtimeAgo
        if mtimeAgo > 30.0:
            nc = netCDF4.Dataset(inFile)
            ntimes = len(nc.dimensions['Time'])
            nc.close()
            ##
            if ntimes == 12:
                outFile = inFile.upper()
                outFile = outFile.replace('_D','_d') # previous upper method also capitalizes domain names which breaks consistency with MCIP
                timeBits = inFile.split('_')
                timestr = '_'.join(timeBits[2:])
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
