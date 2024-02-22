'''Run MCIP from python

The set-up provided assumes that the WRF model output will be in one
file per simulation (rather than one file per hour, or per six hours),
which reflects the sample WRF model output provided in preparation for
this project. If the user decides to split the WRF model output in
other ways, then this section of the code will need to be modified.

The procedure underlying the Python function that runs MCIP is
described in pseudo-code as follows:

for date in dates:    
  for domain in domains:                                
      Extract the subset of data for this day using ncks
      Modify global attributes as necessary             
      Write MCIP run script based on the template       
      Run MCIP        
      Check whether MCIP finished correctly             
      if MCIP failed: 
          Abort       
      endif           
      Compress to netCDF4 using ncks                    
  endfor              
endfor                
'''

import netCDF4
import datetime
import subprocess
import helper_funcs
import os
import glob
import pdb
import tempfile
import sys
from shutil import copyfile

def runMCIP(dates, domains, metDir, wrfDir, geoDir, ProgDir, APPL, CoordName, GridName, scripts,
            compressWithNco = True, fix_simulation_start_date = True, fix_truelat2 = False, truelat2 = None, wrfRunName = None, doArchiveWrf = False, add_qsnow = False):
    '''Function to run MCIP from python

    Args:
        dates: array of dates to process
        domains: list of which domains should be run?
        metDir: base directory for the MCIP output
        wrfDir: directory containing wrfout_* files
        geoDir: directory containing geo_em.* files
        ProgDir: directory containing the MCIP executable
        APPL: scenario tag (for MCIP). 16-character maximum. list: one per domain
        CoordName: Map projection name (for MCIP). 16-character maximum. list: one per domain
        GridName: Grid name (for MCIP). 16-character maximum. list: one per domain
        scripts: dictionary of scripts, including an entry with the key 'mcipRun'
        compressWithNco: True/False - compress output using ncks?
        fix_simulation_start_date: True/False - adjust the SIMULATION_START_DATE attribute in wrfout files?

    Returns:
        Nothing

    '''

    #########

    tmpfl = tempfile.mktemp(suffix='.tar')
    cwd = os.getcwd()

    ndoms = len(domains)
    datesWRF = [[]] * ndoms 
    nMinsPerInterval = [60] * ndoms

    if False:
        for idom,dom in enumerate(domains):
            timesChar = []
            for idate, date in enumerate(dates):
                yyyymmddhh = date.strftime('%Y%m%d%H')
                times = [date + datetime.timedelta(seconds = h*60*60) for h in range(24+1)]
                for itime, time in enumerate(times):
                    WRFfile = '{}/{}/WRFOUT_{}_{}'.format(wrfDir, yyyymmddhh, dom, time.strftime('%Y-%m-%d_%H:%M:%S'))
                    if not os.path.exists(WRFfile):
                        raise RuntimeError("File {} not found...")
                    ##
                    nc  = netCDF4.Dataset(WRFfile)
                    timeschar = nc.variables['Times'][:]
                    nc.close()
                    timesChar.append([''.join(row) for row in timeschar])
            ##
            flatten = lambda l: [item for sublist in l for item in sublist]
            timesChar = flatten(timesChar)
            try:
                datesWRF[idom] = [datetime.datetime.strptime(d, '%Y-%m-%d_%H:%M:%S') for d in timesChar]
            except:
                pdb.set_trace()
            nMinsPerInterval[idom] = (datesWRF[idom][1] - datesWRF[idom][0]).total_seconds()/60.0

    if not os.path.exists(metDir):
        os.mkdir(metDir)
    ##
    for idate, date in enumerate(dates):
        yyyyjjj = date.strftime('%Y%j')
        yyyymmdd = date.strftime('%Y%m%d')
        yyyymmdd_dashed = date.strftime('%Y-%m-%d')
        yyyymmddhh = date.strftime('%Y%m%d%H')
        ##
        parent_mcipdir = '{}/{}'.format(metDir,yyyymmdd_dashed)
        ## create output destination
        if not os.path.exists(parent_mcipdir):
            os.mkdir(parent_mcipdir)
        for idomain, domain in enumerate(domains):
            mcipDir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
            ## create output destination
            if not os.path.exists(mcipDir):
                os.mkdir(mcipDir)

    for idate, date in enumerate(dates):
        print("date =",date)
        yyyymmddhh = date.strftime('%Y%m%d%H')
        yyyymmdd_dashed = date.strftime('%Y-%m-%d')
        for idom, dom in enumerate(domains):
            print('\tdom =',dom)
            ##
            mcipDir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,dom)
            nextDate = date + datetime.timedelta(days = 1)
            ##
            times = [date + datetime.timedelta(seconds = h*60*60) for h in range(24)]
            WRFfiles = [ '{}/{}/WRFOUT_{}_{}'.format(wrfDir, yyyymmddhh, dom, time.strftime('%Y-%m-%d_%H:%M:%S')) for time in times ]
            next_yyyymmddhh = nextDate.strftime('%Y%m%d%H')
            nextDayFile ='{}/{}/WRFOUT_{}_{}'.format(wrfDir, next_yyyymmddhh, dom, nextDate.strftime('%Y-%m-%d_%H:%M:%S'))
            WRFfiles.append( nextDayFile)
            ##
            for WRFfile in WRFfiles:
                src = WRFfile
                assert os.path.exists(src), "file {} not found...".format(src)
                dst = '{}/{}'.format(mcipDir, os.path.basename(WRFfile))
                copyfile(src,dst)
               # print "copy {} to {}".format(src,dst)
            ##the above line is uncommented by Sougol
            ## print 1. # WRF files =',len([f for f in os.listdir(mcipDir) if f.startswith('wrfout_')])
            
            if fix_simulation_start_date:
                print("\t\tFix up SIMULATION_START_DATE attribute with ncatted")
                wrfstrttime = date.strftime('%Y-%m-%d_%H:%M:%S')
                for WRFfile in WRFfiles:
                    outPath = '{}/{}'.format(mcipDir,os.path.basename( WRFfile))
                    command = 'ncatted -O -a SIMULATION_START_DATE,global,m,c,{} {} {}'.format(wrfstrttime,outPath,outPath)
                    print('\t\t\t'+command)
                    commandList = command.split(' ')        
                    ##
                    p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if len(stderr) > 0:
                        print("stdout = " + str(stdout))
                        print("stderr = " + str(stderr))
                        raise RuntimeError("Error from atted...")

            if add_qsnow:
                print("\t\tAdd an artificial variable ('QSNOW') to the WRFOUT files")
                wrfstrttime = date.strftime('%Y-%m-%d_%H:%M:%S')
                for WRFfile in WRFfiles:
                    outPath = '{}/{}'.format(mcipDir,WRFfile)
                    nc = netCDF4.Dataset(outPath,'a')
                    res = nc.createVariable('QSNOW', 'f4',
                                            ('Time', 'bottom_top', 'south_north', 'west_east'),
                                            zlib = True)
                    nc.variables['QSNOW'][:] = 0.0
                    nc.close()
                    
            ## print '2. # WRF files =',len([f for f in os.listdir(mcipDir) if f.startswith('wrfout_')])
            if fix_truelat2 and (truelat2 != None):
                print("\t\tFix up TRUELAT2 attribute with ncatted")
                for WRFfile in WRFfiles:
                    outPath = '{}/{}'.format(mcipDir,WRFfile)
                    command = 'ncatted -O -a TRUELAT2,global,m,f,{} {} {}'.format(truelat2,outPath,outPath)
                    print('\t\t\t'+command)
                    commandList = command.split(' ')        
                    ##
                    p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if len(stderr) > 0:
                        print("stdout = " + stdout)
                        print("stderr = " + stderr)
                        raise RuntimeError("Error from atted...")
            ## print '3. # WRF files =',len([f for f in os.listdir(mcipDir) if f.startswith('wrfout_')])
                    
            ##
            print("\t\tCreate temporary run.mcip script")
            ## pdb.set_trace()
            #{}/{}'.format(wrfDir,date.strftime('%Y%m%d%H'))---by Sougol
            WRFfiles2 = ['{}/{}'.format(mcipDir,ff) for ff in WRFfiles ]
            subs = [['set DataPath   = TEMPLATE', 'set DataPath   = {}'.format(mcipDir)],
                    ['set InMetDir   = TEMPLATE','set InMetDir   = {}'.format(mcipDir)],
                    ['set OutDir     = TEMPLATE', 'set OutDir     = {}'.format(mcipDir)],
                    ['set InMetFiles = ( TEMPLATE )', 'set InMetFiles = ( {} )'.format(' '.join(WRFfiles))],
                    ['set InTerFile  = TEMPLATE', 'set InTerFile  = {}/geo_em.{}.nc'.format(geoDir,dom)],
                    ['set MCIP_START = TEMPLATE', 'set MCIP_START = {}:00:00.0000'.format(date.strftime('%Y-%m-%d-%H'))],
                    ['set MCIP_END   = TEMPLATE', 'set MCIP_END   = {}:00:00.0000'.format(nextDate.strftime('%Y-%m-%d-%H'))],
                    ['set INTVL      = TEMPLATE', 'set INTVL      = {}'.format(int(round(nMinsPerInterval[idom])))],
                    ['set APPL       = TEMPLATE', 'set APPL       = {}'.format(APPL[idom])],
                    ['set CoordName  = TEMPLATE', 'set CoordName  = {}'.format(CoordName[idom])],
                    ['set GridName   = TEMPLATE', 'set GridName   = {}'.format(GridName[idom])],
                    ['set ProgDir    = TEMPLATE', 'set ProgDir    = {}'.format(ProgDir)]]
            ##
            tmpRunMcipPath = '{}/run.mcip.{}.csh'.format(mcipDir,dom)
            helper_funcs.replace_and_write(lines = scripts['mcipRun']['lines'], outfile = tmpRunMcipPath, substitutions = subs, strict = False, makeExecutable = True)
            ##
            ## print '4. # WRF files =',len([f for f in os.listdir(mcipDir) if f.startswith('wrfout_')])
            command = tmpRunMcipPath
            commandList = command.split(' ')
            print('\t\t\t'+command)
            ## delete any existing files
            for metfile in glob.glob("{}/MET*".format(mcipDir)):
                print("rm",metfile)
                #os.remove(metfile)

            for gridfile in glob.glob("{}/GRID*".format(mcipDir)):
                print("rm",gridfile)
                #os.remove(gridfile)

            ## print '5. # WRF files =',len([f for f in os.listdir(mcipDir) if f.startswith('wrfout_')])
            ##
            print("\t\tRun temporary run.mcip script")
            p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = p.communicate()
#            if stdout.split('\n') != 'NORMAL TERMINATION':
#                print "stdout = " + stdout
#                print "stderr = " + stderr
#                raise RuntimeError("Error from run.mcip ...")
            ##

            ## print '6. # WRF files =',len([f for f in os.listdir(mcipDir) if f.startswith('wrfout_')])
            ## sys.exit()
            #for WRFfile in WRFfiles2:
               # os.unlink(WRFfile)
                #the above one is commented by Sougol to avoid deletiobn of wrf files

            if compressWithNco:
                for metfile in glob.glob("{}/MET*_*".format(mcipDir)):
                    print("\t\tCompress {} with ncks".format(metfile))
                    command = 'ncks -4 -L4 -O {} {}'.format(metfile,metfile)
                    print('\t\t\t'+command)
                    commandList = command.split(' ')        
                    ##
                    p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if len(stderr) > 0:
                        print("stdout = " + stdout)
                        print("stderr = " + stderr)
                        raise RuntimeError("Error from ncks...")

                for gridfile in glob.glob("{}/GRID*_*".format(mcipDir)):
                    print("\t\tCompress {} with ncks".format(gridfile))
                    command = 'ncks -4 -L4 -O {} {}'.format(gridfile,gridfile)
                    print('\t\t\t'+command)
                    commandList = command.split(' ')        
                    ##
                    p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    stdout, stderr = p.communicate()
                    if len(stderr) > 0:
                        print("stdout = " + stdout)
                        print("stderr = " + stderr)
                        raise RuntimeError("Error from ncks...")

            if doArchiveWrf and (wrfRunName is not None) and False:
                print('\t\tChecking MCIP output in folder {}'.format(mcipDir))
                ## double check that all the files MCIP files are present before archiving the WRF files
                filetypes = ['GRIDBDY2D', 'GRIDCRO2D', 'GRIDDOT2D', 'METBDY3D', 'METCRO2D', 'METCRO3D', 'METDOT3D']
                for filetype in filetypes:
                    matches = glob.glob("{}/{}_*".format(mcipDir,filetype))
                    if len(matches) != 1:
                        raise RuntimeError("{} file not found in folder {} ... ".format(filetype,mcipDir))
                ##
                thisWRFdir = '{}/{}'.format(wrfDir,yyyymmddhh)
                os.chdir(thisWRFdir)
                ##
                wrfouts = glob.glob("WRFOUT_{}_*".format(dom))
                ##
                command = 'tar -cvf {} {}'.format(tmpfl," ".join(wrfouts))
                print('\t\t\t'+command)
                commandList = command.split(' ')        
                p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if len(stderr) > 0:
                    print("stdout = " + stdout)
                    print("stderr = " + stderr)
                    raise RuntimeError("Error from tar...")
                ##
                command = 'mdss mkdir ns0890/data/WRF/{}/'.format(wrfRunName)
                print('\t\t\t'+command)
                commandList = command.split(' ')
                p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if len(stderr) > 0:
                    print("stdout = " + stdout)
                    print("stderr = " + stderr)
                    raise RuntimeError("Error from mdss...")
                ##
                command = 'mdss put {} ns0890/data/WRF/{}/WRFOUT_{}_{}.tar'.format(tmpfl,wrfRunName,yyyymmddhh,dom)
                print('\t\t\t'+command)
                commandList = command.split(' ')
                p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if len(stderr) > 0:
                    print("stdout = " + stdout)
                    print("stderr = " + stderr)
                    raise RuntimeError("Error from mdss...")
                ##
                command = 'rm -f {}'.format(tmpfl)
                print('\t\t\t'+command)
                commandList = command.split(' ')
                p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if len(stderr) > 0:
                    print("stdout = " + stdout)
                    print("stderr = " + stderr)
                    raise RuntimeError("Error from rm...")
                ##
                command = 'rm {}'.format(" ".join(wrfouts))
                print('\t\t\t'+command)
                commandList = command.split(' ')        
                p = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = p.communicate()
                if len(stderr) > 0:
                    print("stdout = " + stdout)
                    print("stderr = " + stderr)
                    raise RuntimeError("Error from rm...")
                ##
                os.chdir(cwd)
                
