""" Config for CMAQ """
# TODO: Should this better be json like the WRF configs? Here we can take advantage of f-strings

## The main routine controlling the CMAQ preparation phase
#
# Most of the important variables are set here. These are:
# - CMAQdir:  base directory for the CMAQ model
# - MCIPdir:  directory containing the MCIP executable
# - templateDir:  folder containing the template run scripts
# - metDir: base directory for the MCIP output
# - ctmDir: base directory for the CCTM inputs and outputs
# - wrfDir: directory containing wrfout_* files
# - geoDir: directory containing geo_em.* files
# - tempDir: directory for temporary files
# - cmaqEnvScript: path to the (bash) shell script that sets all of the run-time variables for CMAQ (e.g. LD_LIBRARY_PATH, module load <name>, etc.)
# - domains: list of which domains should be run?
# - run: name of the simulation, appears in some filenames (keep this *short* - longer)
# - startDate: this is the START of the first day
# - endDate: this is the START of the last day
# - nhoursPerRun: number of hours to run at a time (24 means run a whole day at once)
# - printFreqHours: frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly
# - mech: name of chemical mechanism to appear in filenames
# - mechCMAQ: name of chemical mechanism given to CMAQ (should be one of: cb05e51_ae6_aq, cb05mp51_ae6_aq, cb05tucl_ae6_aq, cb05tump_ae6_aq, racm2_ae6_aq, saprc07tb_ae6_aq, saprc07tc_ae6_aq, saprc07tic_ae6i_aq, saprc07tic_ae6i_aqkmti)
# - prepareEmis: prepare the emission files
# - prepareICandBC: prepare the initial and boundary conditions from global MOZART output
# - prepareRunScripts: prepare the run scripts
# - forceUpdateMcip: force the update of the MCIP files
# - forceUpdateICandBC: force an update of the initial and boundary conditions from global MOZART output
# - forceUpdateRunScripts: force an update to the run scripts
# - scenarioTag: scenario tag (for MCIP). 16-character maximum
# - mapProjName: Map projection name (for MCIP). 16-character maximum
# - gridName: Grid name (for MCIP). 16-character maximum
# - doCompress: compress the output from netCDF3 to netCDF4 during the CMAQ run
# - compressScript: script to find and compress netCDF3 to netCDF4
# - scripts: This is a dictionary with paths to each of the run-scripts.
# Elements of the dictionary should themselves be dictionaries, with the key
# 'path' and the value being the path to that file. The keys of the 'scripts' dictionary
# should be as follow: mcipRun: MCIP run script; bconRun: BCON run script; iconRun: ICON run
# script; cctmRun: CCTM run script; cmaqRun: main CMAQ run script.

import datetime

# TODO: Remove comments here. Docs should go in Class definition

templateDir = "/opt/project/templateRunScripts"  ## folder containing the template run scripts

config = {
    ## directories
    "CMAQdir" : "/opt/cmaq/CMAQv5.0.2_notpollen/",  ## base directory for the CMAQ model
    "MCIPdir" : "/opt/cmaq/CMAQv5.0.2_notpollen/scripts/mcip/src",  ## directory containing the MCIP executable
    "templateDir" : "/opt/project/templateRunScripts",  ## folder containing the template run scripts
    "metDir" : "/opt/project/data/mcip/",  ## base directory for the MCIP output
    ## convention for MCIP output is that we have data organised by day and domain, eg metDir/2016-11-29/d03
    "ctmDir" : "/opt/project/data/cmaq/",  ## base directory for the CCTM inputs and outputs
    ## same convention for the CMAQ output as for the MCIP output, except with ctmDir
    "wrfDir" : "/opt/project/data/runs/aust-test",  ## directory containing wrfout_* files
    ## convention for WRF output, is wrfDir/2016112900/wrfout_d03_*
    "geoDir" : "/opt/project/templates/aust-test/",  ## directory containing geo_em.* files
    "inputCAMSFile" : "/opt/project/data/inputs/cams_eac4_methane.nc",
    "sufadj" : "output_newMet",
    # this is added by sougol to match the name of the folder created by running adj executable.
    "domains" : ["d01"],  ## which domains should be run?
    "run" : "openmethane",  ## name of the simulation, appears in some filenames (keep this *short* - longer)
    "startDate" : datetime.datetime(2022, 7, 1, 0, 0, 0),  ## this is the START of the first day
    "endDate" : datetime.datetime(2022, 7, 1, 0, 0),  ## this is the START of the last day
    "nhoursPerRun" : 24,  ## number of hours to run at a time (24 means run a whole day at once)
    "printFreqHours" : 1,
    ## frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly
    ## preparation
    "mech" : "CH4only",  ## name of chemical mechanism to appear in filenames
    "mechCMAQ" : "CH4only",
    ## name of chemical mechanism given to CMAQ (should be one of: cb05e51_ae6_aq, cb05mp51_ae6_aq, cb05tucl_ae6_aq, cb05tump_ae6_aq,
    # racm2_ae6_aq, saprc07tb_ae6_aq, saprc07tc_ae6_aq, saprc07tic_ae6i_aq, saprc07tic_ae6i_aqkmti)
    "prepareICandBC" : True,  # prepare the initial and boundary conditions from global CAMS output
    "prepareRunScripts" : True,  # prepare the run scripts
    ## MCIP options
    "add_qsnow" : False,  ## add the 'QSNOW' variable to the WRFOUT files before running MCIP
    "forceUpdateMcip" : False,  # force the update of the MCIP files
    "forceUpdateICandBC" : (
        True  # force an update of the initial and boundary conditions from global MOZART output
    ),
    "forceUpdateRunScripts" : True,  # force an update to the run scripts
    "scenarioTag" : ["220701_aust-test"],  # scenario tag (for MCIP). 16-character maximum
    "mapProjName" : ["LamCon_34S_150E"],  # Map projection name (for MCIP). 16-character maximum
    "gridName" : ["openmethane"],  # Grid name (for MCIP). 16-character maximum
    "doCompress" : True,  ## compress the output from netCDF3 to netCDF4 during the CMAQ run
    "compressScript" : "/opt/project/nccopy_compress_output.sh",  ## script to find and compress netCDF3 to netCDF4
    ## This is a dictionary with paths to each of the
    ## run-scripts. Elements of the dictionary should themselves be
    ## dictionaries, with the key 'path' and the value being the path
    ## to that file. The keys of the 'scripts' dictionary should be as follow:
    # mcipRun - MCIP run script
    # bconRun - BCON run script
    # iconRun - ICON run script
    # cctmRun - CCTM run script
    # cmaqRun - main CMAQ run script
    "scripts" : {
        "mcipRun" : {"path" : f"{templateDir}/run.mcip"},
        "bconRun" : {"path" : f"{templateDir}/run.bcon"},
        "iconRun" : {"path" : f"{templateDir}/run.icon"},
        "cctmRun" : {"path" : f"{templateDir}/run.cctm"},
        "cmaqRun" : {"path" : f"{templateDir}/runCMAQ.sh"},
    },
}
