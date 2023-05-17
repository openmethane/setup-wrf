'''Prepare JPROC photolysis rate-constant files
'''
import os
import datetime
import subprocess
import helper_funcs

# def check_jproc_daily_files_exist(ctmDir, domains, dates, run, GridNames:
#     jproc_files_exist = True
#     for dom, grid in zip(domains, GridNames):
#         for date in dates:
#             yyyymmdd_dashed = date.strftime('%Y-%m-%d')
#             yyyymmddhh = date.strftime('%Y%m%d%H')
#             yyyyjjj = date.strftime('%Y%j')
#             outdir = "{}/{}/{}".format(ctmDir,yyyymmdd_dashed,dom)
#             outfile = '{}/JPROCv2.10.{}.{}.{}.ncf'.format(outdir,grid,mechJPROC,yyyyjjj)
#             exists = os.path.exists(outfile)
#             if not exists:
#                 jproc_files_exist = False
#                 print "File {} not found - will rerun JPROC daily scripts...".format(outfile)
#                 ##
#                 break
#         ##
#         if not jproc_files_exist:
#             break
#     ##
#     return jproc_files_exist

def prepareJprocFiles(dates,scripts,ctmDir,CMAQdir,photDir,mechCMAQ,forceUpdate):
    '''Function to prepare JPROC photolysis rate-constant files

    Args: 
        dates: the dates in question (a list of  datetime objects)
        scripts: dictionary of scripts, including an entry with the key 'jprocRun'
        ctmDir: base directory for the CCTM inputs and outputs
        CMAQdir: base directory for the CMAQ model
        photDir: path to the photolysis data files
        mechCMAQ: name of chemical mechanism given to CMAQ
        forceUpdate: Boolean (True/False) for whether we should update the output if it already exists

    Returns:
        Nothing

    '''
    print "\tPrepare jproc files"
    for idate, date in enumerate(dates):
        yyyyjjj = date.strftime('%Y%j')
        yyyymmdd = date.strftime('%Y%m%d')
        yyyymmdd_dashed = date.strftime('%Y-%m-%d')
        yyyymmddhh = date.strftime('%Y%m%d%H')
        ## check if the required JPROC file is present:
        outdir = '{}/{}'.format(ctmDir,yyyymmdd_dashed)
        JPROCoutput = '{}/JTABLE_{}'.format(outdir,yyyyjjj)
        print "\t\tCheck that JPROC output is available for date = {}".format(yyyymmdd_dashed)
        if not os.path.exists(JPROCoutput) or forceUpdate:
            ## prepare the run script
            print "\t\tPrepare JPROC run script for date = {}".format(yyyymmdd_dashed)
            subsJproc = [['source TEMPLATE','source {}/scripts/config.cmaq'.format(CMAQdir)],
                         ['set BASE = TEMPLATE',    'set BASE = {}'.format(CMAQdir)],
                         ['set PHOTDIR = TEMPLATE', 'set PHOTDIR = {}'.format(photDir)],
                         ['set MECH = TEMPLATE',    'set MECH = {}'.format(mechCMAQ)],
                         ['set STDATE = TEMPLATE',  'set STDATE   = {}'.format(yyyyjjj)],
                         ['set ENDATE = TEMPLATE',  'set ENDATE   = {}'.format(yyyyjjj)],
                         ['set OUTDIR = TEMPLATE',  'set OUTDIR = {}'.format(outdir)]]
            ## adjust CCTM script
            outJprocFile = '{}/run.jproc'.format(outdir)
            helper_funcs.replace_and_write(scripts['jprocRun']['lines'], outJprocFile, subsJproc)
            ## run jproc
            print "\t\tRun JPROC for date {}".format(yyyymmdd)
            os.chmod(outJprocFile,0o0744)
            process = subprocess.Popen(outJprocFile, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (output, err) = process.communicate()
            exit_code = process.wait()
            print outJprocFile
            print err
            print output
            #if exit_code != 0 or len(err) > 0:
             #   print err
              #  raise RuntimeError('Failure in JPROC')

