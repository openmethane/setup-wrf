'''Autogenerate run scripts for the CCTM, BCON and ICON, as well as higher-level run scripts
'''
import os
from setup_runs.utils import replace_and_write, compressNCfile
import subprocess

def prepareCctmRunScripts(dates, domains, ctmDir, metDir, CMAQdir, CFG, mech, mechCMAQ, GridNames, mcipsuffix, scripts, EXEC, SZpath, forceUpdate,nhours = 24, printFreqHours = 1):
    '''Prepare one run script for CCTM per domain per day

    Args: 
        dates: the dates in question (list of datetime objects)
        domains: list of which domains should be run?
        ctmDir: base directory for the CCTM inputs and outputs
        metDir: base directory for the MCIP output
        CMAQdir: base directory for the CMAQ model
        CFG: name of the simulation, appears in some filenames
        mech: name of chemical mechanism to appear in filenames
        mechCMAQ: name of chemical mechanism given to CMAQ
        GridNames: list of MCIP map projection names (one per domain)
        mcipsuffix: Suffix for the MCIP output fileso
        scripts: dictionary of scripts, including an entry with the key 'cctmRun'
        EXEC: The name of the CCTM executable
        SZpath: Folder containing the surfzone files
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists
        nhours: number of hours to run at a time (24 means run a whole day at once)
        printFreqHours: frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly

    Returns:
        Nothing
    
    '''
    
    for idate, date in enumerate(dates):
        yyyyjjj = date.strftime('%Y%j')
        yyyymmdd = date.strftime('%Y%m%d')
        yyyy = date.strftime('%Y')
        yy = date.strftime('%y')
        mm = date.strftime('%m')
        dd = date.strftime('%d')
        yyyymmdd_dashed = date.strftime('%Y-%m-%d')
        hhmmss = date.strftime('%H%M%S')
        duration = '{:02d}0000'.format(nhours)
        if printFreqHours >= 1:
            tstep = '{:02d}0000'.format(printFreqHours)
        else:
            raise RuntimeError('argument printFreqHours currently not configured for sub-hourly output...')
        ##
        if idate != 0:
            lastdate = dates[idate-1]
            lastyyyymmdd = lastdate.strftime('%Y%m%d')
            lastyyyymmdd_dashed = lastdate.strftime('%Y-%m-%d')
        ##
        for idomain, domain in enumerate(domains):
            mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
            chemdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
            chemdatedir = '{}/{}'.format(ctmDir,yyyymmdd_dashed)
            outCctmFile = '{}/run.cctm_{}_{}'.format(chemdir,domain,yyyymmdd)
            if os.path.exists(outCctmFile) and not forceUpdate:
                 continue
            ##
            grid = GridNames[idomain]
            if idate == 0:
                ICONdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
                ICfile = 'ICON.{}.{}.{}.nc'.format(domain,grid,mech)
            else:
                lastCTM_APPL = '{}_{}'.format(CFG, lastyyyymmdd)
                ICONdir = '{}/{}/{}'.format(ctmDir,lastyyyymmdd_dashed,domain)
                ICfile = '{}.CGRID.{}'.format(EXEC.strip(), lastCTM_APPL.strip())
            ##
            BCfile = 'BCON.{}.{}.{}.nc'.format(domain,grid,mech)

            EMISfile  = 'Allmerged_emis_{}_{}.nc'.format(yyyymmdd_dashed,domain)
            #print("emisfile= ",EMISfile)
                
            subsCctm = [['source TEMPLATE/config.cmaq','source {}/scripts/config.cmaq'.format(CMAQdir)],
                        ['set CFG = TEMPLATE',               'set CFG = {}'.format(CFG)],   
                        ['set MECH = TEMPLATE',              'set MECH = {}'.format(mechCMAQ)],   
                        ['set STDATE = TEMPLATE',            'set STDATE = {}'.format(yyyyjjj)],   
                        ['set STTIME = TEMPLATE',            'set STTIME = {}'.format(hhmmss)],   
                        ['set NSTEPS = TEMPLATE',            'set NSTEPS = {}'.format(duration)],   
                        ['set TSTEP = TEMPLATE',             'set TSTEP = {}'.format(tstep)],    
                        ['set YEAR = TEMPLATE',              'set YEAR = {}'.format(yyyy)],     
                        ['set YR = TEMPLATE',                'set YR = {}'.format(yy)],       
                        ['set MONTH = TEMPLATE',             'set MONTH = {}'.format(mm)],    
                        ['set DAY = TEMPLATE',               'set DAY = {}'.format(dd)],      
                        ['setenv GRID_NAME TEMPLATE',        'setenv GRID_NAME {}'.format(grid)],       
                        ['setenv GRIDDESC TEMPLATE/GRIDDESC','setenv GRIDDESC {}/GRIDDESC'.format(mcipdir)],
                        ['set ICpath = TEMPLATE',            'set ICpath = {}'.format(ICONdir)],
                        ['set BCpath = TEMPLATE',            'set BCpath = {}'.format(chemdir)],       
                        ['set EMISpath = TEMPLATE',          'set EMISpath = {}'.format(chemdir)],     
                        ['set METpath = TEMPLATE',           'set METpath = {}'.format(mcipdir)],      
                        ['set JVALpath = TEMPLATE',          'set JVALpath = {}'.format(chemdatedir)],
                        ['set LUpath = TEMPLATE',            'set LUpath = {}'.format(mcipdir)],
                        ['set SZpath = TEMPLATE',            'set SZpath = {}'.format(SZpath)],     
                        ['setenv OCEAN_1 $SZpath/TEMPLATE',  'setenv OCEAN_1 $SZpath/surfzone_{}.nc'.format(domain)],
                        ['set OUTDIR = TEMPLATE',            'set OUTDIR = {}'.format(chemdir)],       
                        ['set ICFILE = TEMPLATE',            'set ICFILE = {}'.format(ICfile)],   
                        ['set BCFILE = TEMPLATE',            'set BCFILE = {}'.format(BCfile)],   
                        ['set EXTN = TEMPLATE',              'set EXTN = {}'.format(mcipsuffix[idomain])],   
                        ['set EMISfile = TEMPLATE',          'set EMISfile = {}'.format(EMISfile)]]
            ##
            ## adjust CCTM script
            print("Prepare CMAQ script for date = {} and domain = {}".format(date.strftime('%Y%m%d'),domain))
            replace_and_write(scripts['cctmRun']['lines'], outCctmFile, subsCctm)
            print(outCctmFile)
            os.chmod(outCctmFile,0o0744)
    return

def prepareBconRunScripts(sufadjname, dates, domains, ctmDir, metDir, CMAQdir, CFG, mech, mechCMAQ, GridNames, mcipsuffix, scripts, forceUpdate):
    '''Prepare run scripts for BCON, one per domain per day

    Args:
        dates: the dates in question (list of datetime objects)
        domains: list of which domains should be run?
        ctmDir: base directory for the CCTM inputs and outputs
        metDir: base directory for the MCIP output
        CMAQdir: base directory for the CMAQ model
        CFG: name of the simulation, appears in some filenames
        mech: name of chemical mechanism to appear in filenames
        mechCMAQ: name of chemical mechanism given to CMAQ
        GridNames: list of MCIP map projection names (one per domain)
        mcipsuffix: Suffix for the MCIP output files
        scripts: dictionary of scripts, including an entry with the key 'bconRun'
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists

    Returns:
        Nothing
    '''

    inputType = 'm3conc'
    for idate, date in enumerate(dates):
        yyyyjjj = date.strftime('%Y%j')
        yyyymmdd = date.strftime('%Y%m%d')
        yyyymmdd_dashed = date.strftime('%Y-%m-%d')

        for idomain, domain in enumerate(domains):
            mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
            chemdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
            grid = GridNames[idomain]
            ##
            ## adjust BCON script
            if idomain != 0:
                lastmcipdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domains[idomain-1])

                outBconFile = '{}/run.bcon_{}_{}'.format(chemdir,domain,yyyymmdd)
                if os.path.exists(outBconFile) and not forceUpdate:
                    continue
                ##
                outfile = 'BCON.{}.{}.{}.nc'.format(domain,grid,mech)
                input3Dconfile = '{}/{}_{}_{}/CONC.{}'.format(ctmDir,mech, domains[idomain-1],sufadjname,yyyymmdd)
                MetCro3dCrs = '{}/METCRO3D_{}'.format(lastmcipdir,mcipsuffix[idomain-1])
                MetCro3dFin = '{}/METCRO3D_{}'.format(mcipdir,mcipsuffix[idomain])
                subsBcon = [['source TEMPLATE/config.cmaq',                  'source {}/scripts/config.cmaq'.format(CMAQdir)],
                            ['set BC = TEMPLATE',                            'set BC = {}'.format(inputType)],
                            ['set DATE = TEMPLATE',                          'set DATE = {}'.format(yyyyjjj)],
                            ['set CFG      = TEMPLATE',                      'set CFG      = {}'.format(CFG)],  
                            ['set MECH     = TEMPLATE',                      'set MECH     = {}'.format(mechCMAQ)],  
                            ['setenv GRID_NAME TEMPLATE',                    'setenv GRID_NAME {}'.format(grid)],       
                            ['setenv GRIDDESC TEMPLATE/GRIDDESC',            'setenv GRIDDESC {}/GRIDDESC'.format(mcipdir)],
                            ['setenv LAYER_FILE TEMPLATE/METCRO3D_TEMPLATE', 'setenv LAYER_FILE {}'.format(MetCro3dFin)],
                            ['setenv OUTDIR TEMPLATE'  ,                     'setenv OUTDIR {}'.format(chemdir)],
                            ['setenv OUTFILE TEMPLATE',                      'setenv OUTFILE {}'.format(outfile)],
                            ['setenv CTM_CONC_1 TEMPLATE',                   'setenv CTM_CONC_1 {}'.format(input3Dconfile)],     
                            ['setenv MET_CRO_3D_CRS TEMPLATE',               'setenv MET_CRO_3D_CRS {}'.format(MetCro3dCrs)], 
                            ['setenv MET_CRO_3D_FIN TEMPLATE',               'setenv MET_CRO_3D_FIN {}'.format(MetCro3dFin)]]
                ##
                print("Prepare BCON script for date = {} and domain = {}".format(date.strftime('%Y%m%d'),domain))
                replace_and_write(scripts['bconRun']['lines'], outBconFile, subsBcon)
                os.chmod(outBconFile,0o0744)
    return

def prepareTemplateBconFiles(date, domains, ctmDir, metDir, CMAQdir, CFG, mech, GridNames, mcipsuffix, scripts, forceUpdate):
    '''Prepare template BC files using BCON

    Args:
        dates: the dates in question (list of datetime objects)
        domains: list of which domains should be run?
        ctmDir: base directory for the CCTM inputs and outputs
        metDir: base directory for the MCIP output
        CMAQdir: base directory for the CMAQ model
        CFG: name of the simulation, appears in some filenames
        mech: name of chemical mechanism to appear in filenames
        GridNames: list of MCIP map projection names (one per domain)
        mcipsuffix: Suffix for the MCIP output files
        scripts: dictionary of scripts, including an entry with the key 'bconRun'
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists

    Returns:
        list of the template BCON files (one per domain)
    '''
    
    ##
    yyyyjjj = date.strftime('%Y%j')
    yyyymmdd = date.strftime('%Y%m%d')
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')
    ##
    ndom = len(domains)
    outputFiles = [''] * ndom
    inputType = 'profile'
    for idomain, domain in enumerate(domains):
        mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
        grid = GridNames[idomain]
        outfile = 'template_bcon_profile_{}_{}.nc'.format(mech,domain)
        outpath = '{}/{}'.format(ctmDir,outfile)
        outputFiles[idomain] = outpath
        if os.path.exists(outpath):
            if forceUpdate:
                ## BCON does not like it if the destination file exits
                os.remove(outpath)
            else:
                continue
        ##
        ## adjust BCON script
        outBconFile = '{}/run.bcon'.format(ctmDir,domain,yyyymmdd)
        ##
        subsBcon = [['source TEMPLATE/config.cmaq',                  'source {}/scripts/config.cmaq'.format(CMAQdir)],
                    ['set BC = TEMPLATE',                            'set BC = {}'.format(inputType)],
                    ['set DATE = TEMPLATE',                          'set DATE = {}'.format(yyyyjjj)],
                    ['set CFG      = TEMPLATE',                      'set CFG      = {}'.format(CFG)],  
                    ['set MECH     = TEMPLATE',                      'set MECH     = {}'.format(mech)],  
                    ['setenv GRID_NAME TEMPLATE',                    'setenv GRID_NAME {}'.format(grid)],       
                    ['setenv GRIDDESC TEMPLATE/GRIDDESC',            'setenv GRIDDESC {}/GRIDDESC'.format(mcipdir)],
                    ['setenv LAYER_FILE TEMPLATE/METCRO3D_TEMPLATE', 'setenv LAYER_FILE {}/METCRO3D_{}'.format(mcipdir,mcipsuffix[idomain])],
                    ['setenv OUTDIR TEMPLATE',                        'setenv OUTDIR {}'.format(ctmDir)],
                    ['setenv OUTFILE TEMPLATE',                       'setenv OUTFILE {}'.format(outfile)]]
        ##
        print("Prepare BCON script for domain = {}".format(domain))
        replace_and_write(scripts['bconRun']['lines'], outBconFile, subsBcon)
        os.chmod(outBconFile,0o0744)
        ##
        print("Run BCON")
        commandList = [outBconFile]
        process = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        try:
          if output.decode().find('Program  BCON completed successfully') < 0:
              print(outBconFile)
              print('exit_code = ',exit_code)
              print('err =',err.decode())
              print('output =', output.decode())
              raise RuntimeError('failure in bcon')
        except Exception:
            raise
        ##
        print("Compress the output file")
        filename = '{}/{}'.format(ctmDir, outfile)
        compressNCfile(filename)
        outputFiles[idomain] = filename
    ##
    
    return outputFiles

def prepareMainRunScript(dates, domains, ctmDir, CMAQdir, scripts, doCompress, compressScript, run, forceUpdate):
    '''Setup the higher-level run-script

    Args:
        dates: the dates in question (list of datetime objects)
        domains: list of which domains should be run?
        ctmDir: base directory for the CCTM inputs and outputs
        CMAQdir: base directory for the CMAQ model
        scripts: dictionary of scripts, including an entry with the key 'cmaqRun'
        doCompress: Boolean (True/False) for whether the output should be compressed to netCDF4 during the simulation
        compressScript: script to find and compress netCDF3 to netCDF4
        run: name of the simulation, appears in some filenames
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists

    Returns:
        Nothing
    '''
    
    ##
    outfile = 'runCMAQ.sh'
    outpath = '{}/{}'.format(ctmDir,outfile)
    if os.path.exists(outpath) and (not forceUpdate):
        return
    ##
    subsCMAQ = [['STDATE=TEMPLATE',          'STDATE={}'.format(dates[0].strftime('%Y%m%d'))],         
                ['ENDATE=TEMPLATE',          'ENDATE={}'.format(dates[-1].strftime('%Y%m%d'))],         
                ['domains=(TEMPLATE)',       'domains=({})'.format(' '.join(domains))],      
                ['cmaqDir=TEMPLATE',         'cmaqDir={}'.format(CMAQdir)],        
                ['ctmDir=TEMPLATE',          'ctmDir={}'.format(ctmDir)],         
                ['doCompress=TEMPLATE',      'doCompress={}'.format(str(doCompress).lower())],
                ['run=TEMPLATE',             'run={}'.format(run)],
                ['compressScript=TEMPLATE',  'compressScript={}'.format(compressScript)]]
    ##
    print("Prepare the global CMAQ run script")
    replace_and_write(scripts['cmaqRun']['lines'], outpath, subsCMAQ)
    os.chmod(outpath,0o0744)
    return


def prepareTemplateIconFiles(date, domains, ctmDir, metDir, CMAQdir, CFG, mech, GridNames, mcipsuffix, scripts, forceUpdate):
    '''Prepare template IC files using ICON

    Args:
        dates: the dates in question (list of datetime objects)
        domains: list of which domains should be run?
        ctmDir: base directory for the CCTM inputs and outputs
        metDir: base directory for the MCIP output
        CMAQdir: base directory for the CMAQ model
        CFG: name of the simulation, appears in some filenames
        mech: name of chemical mechanism to appear in filenames
        GridNames: list of MCIP map projection names (one per domain)
        mcipsuffix: Suffix for the MCIP output files
        scripts: dictionary of scripts, including an entry with the key 'iconRun'
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists

    Returns:
        list of the template ICON files (one per domain)
    '''
    ##
    yyyyjjj = date.strftime('%Y%j')
    yyyymmdd = date.strftime('%Y%m%d')
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')

    ndom = len(domains)
    outputFiles = [''] * ndom
    inputType = 'profile'
    for idomain, domain in enumerate(domains):
        mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
        grid = GridNames[idomain]
        outfile = 'template_icon_profile_{}_{}.nc'.format(mech,domain)
        outpath = '{}/{}'.format(ctmDir,outfile)
        outputFiles[idomain] = outpath
        if os.path.exists(outpath):
            if forceUpdate:
                ## ICON does not like it if the destination file exists
                os.remove(outpath)
            else:
                continue
        ##
        ## adjust ICON script
        outIconFile = '{}/run.icon'.format(ctmDir,domain,yyyymmdd)
        ##
        subsIcon = [['source TEMPLATE/config.cmaq',                  'source {}/scripts/config.cmaq'.format(CMAQdir)],
                    ['set IC = TEMPLATE',                            'set IC = {}'.format(inputType)],
                    ['set DATE = TEMPLATE',                          'set DATE = {}'.format(yyyyjjj)],
                    ['set CFG      = TEMPLATE',                      'set CFG      = {}'.format(CFG)],  
                    ['set MECH     = TEMPLATE',                      'set MECH     = {}'.format(mech)],  
                    ['setenv GRID_NAME TEMPLATE',                    'setenv GRID_NAME {}'.format(grid)],       
                    ['setenv GRIDDESC TEMPLATE/GRIDDESC',            'setenv GRIDDESC {}/GRIDDESC'.format(mcipdir)],
                    ['setenv LAYER_FILE TEMPLATE/METCRO3D_TEMPLATE', 'setenv LAYER_FILE {}/METCRO3D_{}'.format(mcipdir,mcipsuffix[idomain])],
                    ['setenv OUTDIR TEMPLATE',                     'setenv OUTDIR {}'.format(ctmDir)],
                    ['setenv OUTFILE TEMPLATE',                    'setenv OUTFILE {}'.format(outfile)]]
        ##
        print("Prepare ICON script for domain = {}".format(domain))
        replace_and_write(scripts['iconRun']['lines'], outIconFile, subsIcon)
        os.chmod(outIconFile,0o0744)
        ##
        print("Run ICON")
        commandList = [outIconFile]
        process = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if output.decode().find('Program  ICON completed successfully') < 0:
            print(outIconFile)
            print('exit_code = ',exit_code)
            print('err =',err)
            print('output =', output)
            raise RuntimeError('failure in icon')
        ##
        print("Compress the output file")
        filename = '{}/{}'.format(ctmDir, outfile)
        compressNCfile(filename)
    ##
    return outputFiles
               
