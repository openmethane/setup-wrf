'''Prepare MEGAN biogenic emissions
'''
import os
import re
import copy
import datetime
import subprocess
import helper_funcs
import tarfile
import shutil
import glob

def check_megan_input_files_exist(ctmDir, run, domains):
    '''Check if static MEGAN inputs have been produced

    Args:
        ctmDir: base directory for the CCTM inputs and outputs
        run: name of the simulation, appears in some filenames
        domains: list of which domains should be run?

    Retunrs:
        Boolean (True/False) depending on whether all the static MEGAN inputs were found
    '''
    megan_files_exist = True
    for idomain, domain in enumerate(domains):
        efmapsfile = '{}/EFMAPS.{}_{}.ncf'.format(ctmDir, run, domain)
        pfts16file = '{}/PFTS16.{}_{}.ncf'.format(ctmDir, run, domain)
        lais46file = '{}/LAIS46.{}_{}.ncf'.format(ctmDir, run, domain)
        files = [efmapsfile, pfts16file, lais46file]
        exists = [os.path.exists(f) for f in files]
        if not all(exists):
            megan_files_exist = False
            for ifile, exist in enumerate(exists):
                if not exist:
                    print("\t\tFile {} not found - will rerun MEGAN preparation scripts...".format(files[ifile]))
            ##
            break
    ##
    return megan_files_exist

def check_megan_daily_files_exist(ctmDir, domains, dates, run, GridNames, mechMEGAN):
    '''Check if daily MEGAN inputs have been produced

    Args:
        ctmDir: base directory for the CCTM inputs and outputs
        domains: list of which domains should be run?
        dates: the dates in question (list of datetime objects)
        run: name of the simulation, appears in some filenames
        GridNames: list of MCIP map projection names (one per domain)
        mechMEGAN: name of chemical mechanism given to MEGAN

    Retunrs:
        Boolean (True/False) depending on whether all the daily MEGAN inputs were found
    '''
    megan_files_exist = True
    for dom, grid in zip(domains, GridNames):
        for date in dates:
            yyyymmdd_dashed = date.strftime('%Y-%m-%d')
            yyyymmddhh = date.strftime('%Y%m%d%H')
            yyyyjjj = date.strftime('%Y%j')
            outdir = "{}/{}/{}".format(ctmDir,yyyymmdd_dashed,dom)
            outfile = '{}/MEGANv2.10.{}.{}.{}.ncf'.format(outdir,grid,mechMEGAN,yyyyjjj)
            exists = os.path.exists(outfile)
            if not exists:
                megan_files_exist = False
                print("File {} not found - will rerun MEGAN daily scripts...".format(outfile))
                ##
                break
        ##
        if not megan_files_exist:
            break
    ##
    return megan_files_exist

def make_megan_input_files(meganfolder, run, domains, x0, y0, ncolsin, nrowsin, prepdir, scripts, date, wrfDir, tempDir, ctmDir, inputsDir, metDir, GridNames, removeScripts = False, removeTxt2ioapiLogs = True):
    '''Make the static MEGAN input files

    Args:
        meganfolder: base directory for the MEGAN suite
        run: name of the simulation, appears in some filenames
        domains: list of which domains should be run?
        x0: the index in the WRF grid of the first CMAQ grid-point in the x-direction
        y0: the index in the WRF grid of the first CMAQ grid-point in the y-direction
        ncolsin: length of the x-dimension for the CMAQ grid
        nrowsin: length of the y-dimension for the CMAQ grid
        prepdir: base directory for the prepmegan4cmaq suite
        scripts: dictionary of scripts
        date: the date in question (a datetime objects)
        wrfDir: directory containing wrfinp_* files
        tempDir: directory for temporary files
        ctmDir: base directory for the CCTM inputs and outputs
        inputsDir: folder containing leaf area index, plant functional type and emission factor maps required for MEGAN
        metDir: base directory for the MCIP output
        GridNames: list of MCIP map projection names (one per domain)
        removeScripts: Boolean (True/False) whether to remove input scripts once they have finished
        removeTxt2ioapiLogs: Remove log files from TXT2IOAPI (can be large)

    Returns:
        Nothing
    '''
    ndomains = len(domains)
    ## get ready to run the preprocessing for MEGAN
    megandir = meganfolder
    if not os.path.exists(megandir):
        os.mkdir(megandir)
    outPrepFile = '{}/prepmegan4cmaq_{}.inp'.format(ctmDir,run)
    subsPrep = [["domains = TEMPLATE", "domains = {}".format(ndomains)],
                ["wrf_dir = TEMPLATE", "wrf_dir = '{}'".format(wrfDir)],
                ["megan_dir = TEMPLATE", "megan_dir = '{}'".format(inputsDir)],
                ["out_dir = TEMPLATE", "out_dir = '{}'".format(ctmDir)],
                ["runname = TEMPLATE", "runname = '_{}'".format(run)],
                ['x0 = TEMPLATE', 'x0 = {}'.format(helper_funcs.int_array_to_comma_separated_string(x0))],
                ['y0 = TEMPLATE', 'y0 = {}'.format(helper_funcs.int_array_to_comma_separated_string(y0))],
                ['ncolsin = TEMPLATE', 'ncolsin = {}'.format(helper_funcs.int_array_to_comma_separated_string(ncolsin))],
                ['nrowsin = TEMPLATE', 'nrowsin = {}'.format(helper_funcs.int_array_to_comma_separated_string(nrowsin))]]
    helper_funcs.replace_and_write(scripts['prepMegan4Cmaq']['lines'], outPrepFile, subsPrep)

    ## run the MEGAN preprocessing scripts
    print("run prepmegan4cmaq_lai")
    

    foundAllOutputs = True
    for idom,dom in enumerate(domains):
       outfile = os.path.join(ctmDir,'LAI210_{}_{}.csv'.format(run,dom))
       if not os.path.exists(outfile):
           foundAllOutputs = False
    ##
    if not foundAllOutputs:
        commandList = [prepdir + "/prepmegan4cmaq_lai.x", outPrepFile]
        process = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE) ## shell=True, env = envVars
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or len(err) > 0:
            print(" ".join(commandList))
            print('exit_code =',exit_code)
            print('err',err)
            print('output',output)
            raise RuntimeError('failure in prepmegan4cmaq_lai.x')

    foundAllOutputs = True
    for idom,dom in enumerate(domains):
       outfile = os.path.join(ctmDir,'PFT210_{}_{}.csv'.format(run,dom))
       if not os.path.exists(outfile):
           foundAllOutputs = False
    ##
    if not foundAllOutputs:
        print("run prepmegan4cmaq_pft")
        commandList = [prepdir + "/prepmegan4cmaq_pft.x", outPrepFile]
        process = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or len(err) > 0:
            print(" ".join(commandList))
            print('exit_code =',exit_code)
            print('err',err)
            print('output',output)
            raise RuntimeError('failure in prepmegan4cmaq_pft.x')

    foundAllOutputs = True
    for idom,dom in enumerate(domains):
       outfile = os.path.join(ctmDir,'EF210_{}_{}.csv'.format(run,dom))
       if not os.path.exists(outfile):
           foundAllOutputs = False
    ##
    if not foundAllOutputs:
        print("run prepmegan4cmaq_ef")
        commandList = [prepdir + "/prepmegan4cmaq_ef.x", outPrepFile]
        process = subprocess.Popen(commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or len(err) > 0:
            print(" ".join(commandList))
            print('exit_code =',exit_code)
            print('err',err)
            print('output',output)
            raise RuntimeError('failure in prepmegan4cmaq_ef.x')

    yyyymmdd = date.strftime('%Y%m%d')
    yyyymmddhh = date.strftime('%Y%m%d%H')
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')

    outSetcaseFile = '{}/setcase.csh'.format(ctmDir)
    for idomain, domain in enumerate(domains):
        mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
        outTxt2ioapiFile = '{}/{}/{}/txt2ioapi_{}_{}.csh'.format(ctmDir,yyyymmdd_dashed,domain,yyyymmdd,domain)
        ##
        subsMgn = [
            ## lines for setcase
            ['setenv SCRATCHDIR TEMPLATE', 'setenv SCRATCHDIR {}'.format(tempDir)],
            ['setenv MGNHOME TEMPLATE', 'setenv MGNHOME {}'.format(megandir)],
            ['setenv OUTDIR TEMPLATE', 'setenv OUTDIR {}'.format(ctmDir)],
            ['setenv CTMDIR TEMPLATE', 'setenv CTMDIR {}'.format(ctmDir)],
            ## for txt2ioapi
            ['setenv PRJ TEMPLATE', 'setenv PRJ {}'.format(run)],
            ['setenv DOM TEMPLATE', 'setenv DOM {}'.format(domain)],
            ['setenv GDNAM3D TEMPLATE', 'setenv GDNAM3D {}'.format(GridNames[idomain])],
            ['setenv MCIPDIR TEMPLATE', 'setenv MCIPDIR {}'.format(mcipdir)],
            ['source TEMPLATE/setcase.csh', 'source {}'.format(outSetcaseFile)]]
        ##
        helper_funcs.replace_and_write(scripts['megansetcase']['lines'], outSetcaseFile, subsMgn, strict = False, makeExecutable = True)
        helper_funcs.replace_and_write(scripts['txt2ioapi']['lines'], outTxt2ioapiFile, subsMgn, strict = False, makeExecutable = True)
        ## run the MEGAN preprocessing scripts
        print("run txt2ioapi for domain",domain)
        process = subprocess.Popen(outTxt2ioapiFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or output.find('Normal Completion of program TXT2IOAPI') < 0 or len(err) > 0:
            print(outTxt2ioapiFile)
            print('exit_code = ',exit_code)
            print('err =',err)
            print('output =', output)
            raise RuntimeError('failure in txt2ioapi')
    ##
    ## compress inputs
    print("compress the input files")
    tar = tarfile.open("{}/csv_inputs.tar.gz".format(ctmDir), "w:gz")
    files = []
    for domain in domains:
        files.append('{}/EF210_{}_{}.csv'.format(ctmDir,run,domain))
        files.append('{}/LAI210_{}_{}.csv'.format(ctmDir,run,domain))
        files.append('{}/PFT210_{}_{}.csv'.format(ctmDir,run,domain))
    ##
    for f in files:
        tar.add(f)
    ##
    tar.close()
    ## now delete the .csv files (these are now compressed)
    for f in files:
        os.remove(f)
    ## compress outputs
    print("compress the output files ")
    process = subprocess.Popen(["/home/563/ns0890/runCMAQ/compress_netcdf.sh", ctmDir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (output, err) = process.communicate()
    exit_code = process.wait()
    if exit_code != 0 or len(err) > 0:
        raise RuntimeError('failure in nc_compress')
    ## clean up the run scripts
    if removeScripts:
        print("Clean up run scripts")
        outSetcaseFile = '{}/setcase.csh'.format(ctmDir)
        os.remove(outSetcaseFile)
        outPrepFile = '{}/prepmegan4cmaq_{}.inp'.format(ctmDir,run)
        os.remove(outPrepFile)
        for idomain, domain in enumerate(domains):
            outTxt2ioapiFile = '{}/txt2ioapi_{}_{}.csh'.format(ctmDir,yyyymmdd,domain)
            os.remove(outTxt2ioapiFile)
    ## clean up the log files (these can be relatively large)
    if removeTxt2ioapiLogs:
        print("Clean up log files")
        logDir = '{}/txt2ioapi'.format(ctmDir)
        shutil.rmtree(logDir)


def make_megan_daily_outputs(meganfolder,metDir, run, domains, scripts, date, ctmDir, mech, tempDir, GridNames, deleteIntermediates = False):
    '''Calculate the daily biogenic emission files for MEGAN

    Args:
        meganfolder: base directory for the MEGAN suite
        metDir: base directory for the MCIP output
        run: name of the simulation, appears in some filenames
        domains: list of which domains should be run?
        scripts: dictionary of scripts
        date: the date in question (a datetime objects)
        ctmDir: base directory for the CCTM inputs and outputs
        mech: name of chemical mechanism given to MEGAN
        tempDir: directory for temporary files
        GridNames: list of MCIP map projection names (one per domain)
        deleteIntermediates: Boolean (True/False) whether to remove input intermediate files once they have finished

    Returns:
        Nothing
    '''
    ## get ready to run the preprocessing for MEGAN
    ndomains = len(domains)
    megandir = meganfolder
    ##
    mechs = ['RADM2', 'RACM','CBMZ', 'CB05', 'CB6', 'SOAX', 'SAPRC99', 'SAPRC99Q', 'SAPRC99X']
    if not (mech in mechs):
        print("mechanism chosen was {}".format(mech))
        print("options for mechanisms are: {}".format(', '.join(mechs)))
        raise RuntimeError('mechanism not in the list of mechanisms')
    ##
    yyyymmdd = date.strftime('%Y%m%d')
    yyyymmddhh = date.strftime('%Y%m%d%H') 
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')
    yyyyjjj = date.strftime('%Y%j')
    outSetcaseFile = '{}/setcase.csh'.format(ctmDir)
    ##

    ## get ready to run MEGAN
    for idomain, domain in enumerate(domains):
        mcipdir = '{}/{}/{}'.format(metDir,yyyymmdd_dashed,domain)
        outdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
        outMet2mgnFile = '{}/met2mgn_{}_{}.csh'.format(outdir,yyyymmdd,domain)
        outEmprocFile = '{}/emproc_{}_{}.csh'.format(outdir,yyyymmdd,domain)
        outMgn2mechFile = '{}/mgn2mech_{}_{}.csh'.format(outdir,yyyymmdd,domain)
        ## find the suffix for the MCIP files
        filetype = 'GRIDCRO2D'
        matches = glob.glob("{}/{}_*".format(mcipdir,filetype))
        if len(matches) == 0:
            raise RuntimeError("{} file not found in folder {} ... ".format(filetype,mcipdir))
        ##
        mcipSuffix = matches[0].split('/')[-1].replace('{}_'.format(filetype),'')
        print('mcipSuffix = {}'.format(mcipSuffix))
        ##
        subsMgn = [
            ## lines for setcase
            ['setenv SCRATCHDIR TEMPLATE', 'setenv SCRATCHDIR {}'.format(tempDir)],
            ['setenv MGNHOME TEMPLATE', 'setenv MGNHOME {}'.format(megandir)],
            ['setenv CTMDIR TEMPLATE', 'setenv CTMDIR {}'.format(ctmDir)],
            ## for txt2ioapi
            ['setenv PRJ TEMPLATE', 'setenv PRJ {}'.format(run)],
            ['setenv DOM TEMPLATE', 'setenv DOM {}'.format(domain)],
            ['setenv GDNAM3D TEMPLATE', 'setenv GDNAM3D {}'.format(GridNames[idomain])],
            ['setenv MCIPDIR TEMPLATE', 'setenv MCIPDIR {}'.format(mcipdir)],
            ['setenv GRIDDESC $SCRATCHDIR/GRIDDESC_${PRJ}${DOM}', 'setenv GRIDDESC {}/GRIDDESC'.format(mcipdir)],
            ['source TEMPLATE/setcase.csh', 'source {}'.format(outSetcaseFile)],
            ## for met2mgn
            ['set dom = TEMPLATE',            'set dom = {}'.format(domain)],           
            ['set STJD = TEMPLATE',           'set STJD = {}'.format(yyyyjjj)],          
            ['set EDJD = TEMPLATE',           'set EDJD = {}'.format(yyyyjjj)],          
            ['setenv EPISODE_SDATE TEMPLATE', 'setenv EPISODE_SDATE {}'.format(yyyyjjj)],
            ['setenv EPISODE_STIME TEMPLATE', 'setenv EPISODE_STIME {}'.format('000000')],
            ['setenv METPATH TEMPLATE',       'setenv METPATH {}'.format(metDir)],
            ['setenv MCIPSUFFIX TEMPLATE',    'setenv MCIPSUFFIX {}'.format(mcipSuffix)],
            ['set OUTPATH = TEMPLATE', 'set OUTPATH = {}'.format(outdir)],
            ## for emproc
            ['setenv INPDIR TEMPLATE', 'setenv INPDIR {}'.format(ctmDir)],
            ['setenv OUTDIR TEMPLATE', 'setenv OUTDIR {}'.format(outdir)],
            ## for mgn2mech
            ['setenv MECHANISM TEMPLATE','setenv MECHANISM {}'.format(mech)]]
        ## prepare the MEGAN processing scripts
        print("prepare the MEGAN processing scripts for date {} and domain {}".format(yyyymmdd, domain))
        helper_funcs.replace_and_write(scripts['megansetcase']['lines'], outSetcaseFile, subsMgn, strict = False, makeExecutable = True)
        helper_funcs.replace_and_write(scripts['met2mgn']['lines'], outMet2mgnFile, subsMgn, strict = False, makeExecutable = True)
        helper_funcs.replace_and_write(scripts['emproc']['lines'], outEmprocFile, subsMgn, strict = False, makeExecutable = True)
        helper_funcs.replace_and_write(scripts['mgn2mech']['lines'], outMgn2mechFile, subsMgn, strict = False, makeExecutable = True)

        ## run the MEGAN preprocessing scripts
        ## the following need to be done for each day, and each domain
        print("Run met2mgn for date {} and domain {}".format(yyyymmdd, domain))
        process = subprocess.Popen(outMet2mgnFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or output.find('Normal completion by met2mgn') < 0 or len(err) > 0:
            print('exit_code = ',exit_code)
            print('err =',err)
            print('output =', output)
            raise RuntimeError('failure in met2mgn')

        print("Run emproc for date {} and domain {}".format(yyyymmdd, domain))
        process = subprocess.Popen(outEmprocFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or output.find('Normal Completion of program EMPROC') < 0:
            print('exit_code = ',exit_code)
            print('err =',err)
            print('output =', output)
            raise RuntimeError('failure in emproc')

        print("Run mgn2mech for date {} and domain {}".format(yyyymmdd, domain))
        process = subprocess.Popen(outMgn2mechFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, err) = process.communicate()
        exit_code = process.wait()
        if exit_code != 0 or output.find('Normal Completion of program MGN2MECH') < 0 or len(err) > 0:
            print('exit_code = ',exit_code)
            print('err =',err)
            print('output =', output)
            raise RuntimeError('failure in mgn2mech')
        ##
    
    ## cleanup
    ## This temporary file is definitely not needed for anything further
    os.remove('{}/PFILE'.format(outdir))
    ##
    if deleteIntermediates:
        ##
        prefixes = ['ER', 'MET.MEGAN']
        for idomain, domain in enumerate(domains):
            outdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
            for prefix in prefixes:
                filename = '{}/{}.{}_{}.{}.ncf'.format(outdir, prefix, domain, run, yyyyjjj)
                os.remove(filename)
        ##
        prefixes = [ 'emproc', 'met2mgn', 'mgn2mech' ]
        for idomain, domain in enumerate(domains):
            outdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
            for prefix in prefixes:
                filename = '{}/{}_{}_{}.csh'.format(outdir, prefix, yyyymmdd, domain)
                os.remove(filename)

def compressMeganOutputs(domains, GridNames, date, ctmDir, mechMEGAN):
    '''Compress the output from MEGAN from netCDF3 to netCDF4 using ncks

    Args:
        domains: list of which domains should be run?
        GridNames: list of MCIP map projection names (one per domain)
        date: the date in question (a datetime objects)
        ctmDir: base directory for the CCTM inputs and outputs
        mechMEGAN: name of chemical mechanism given to MEGAN

    Returns:
        Nothing

    '''
    ## compress outputs
    yyyyjjj = date.strftime('%Y%j')
    yyyymmdd_dashed = date.strftime('%Y-%m-%d')
    print("Compress the output files ")
    prefixes = ['ER', 'MET.MEGAN']
    for domain, grid in zip(domains, GridNames):
        outdir = '{}/{}/{}'.format(ctmDir,yyyymmdd_dashed,domain)
        for prefix in prefixes:
            filename = '{}/{}.{}.{}.ncf'.format(outdir, prefix, grid, yyyyjjj)
            helper_funcs.compressNCfile(filename)
        ## 
        prefix = 'MEGANv2.10'
        filename = '{}/{}.{}.{}.{}.ncf'.format(outdir, prefix, grid, mechMEGAN, yyyyjjj)
        helper_funcs.compressNCfile(filename)
            
                
    # process = subprocess.Popen(['nc_compress', '--verbose', '--overwrite', outdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # (output, err) = process.communicate()
    # exit_code = process.wait()
    # if exit_code != 0 or len(err) > 0:
    #     raise RuntimeError('failure in nc_compress')

