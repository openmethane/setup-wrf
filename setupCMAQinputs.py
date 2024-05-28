## Top level run script for the preparation phase
#
# This is the top-level script that sets up the CMAQ inputs. Most of
# the detail and functionality is found in a series of accompanying
# files. Tasks performed:
#  - create output destinations (if need be)
#  - check the latitudes and longitudes of the WRF and MCIP grids against one another
#  - prepare run scripts for ICON, BCON and CCTM programs within the CMAQ  bundle
#
# Author: Jeremy Silver (jeremy.silver@unimelb.edu.au)
# Date: 2016-11-04


import datetime

import checkWrfMcipDomainSizes
import configureRunScripts
import helper_funcs
import interpolateFromCAMS
import runMCIP


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
# - scripts: This is a dictionary with paths to each of the run-scripts. Elements of the dictionary should themselves be dictionaries, with the key 'path' and the value being the path to that file. The keys of the 'scripts' dictionary should be as follow: mcipRun: MCIP run script; bconRun: BCON run script; iconRun: ICON run script; cctmRun: CCTM run script; cmaqRun: main CMAQ run script.
def main():
    ################ MOST USER INPUT SHOULD BE BELOW HERE ###################

    ## directories
    CMAQdir = "/opt/cmaq/CMAQv5.0.2_notpollen/"  ## base directory for the CMAQ model
    MCIPdir = "/opt/cmaq/CMAQv5.0.2_notpollen/scripts/mcip/src"  ## directory containing the MCIP executable

    templateDir = "/opt/project/templateRunScripts"  ## folder containing the template run scripts
    metDir = "/opt/project/data/mcip/"  ## base directory for the MCIP output
    ## convention for MCIP output is that we have data organised by day and domain, eg metDir/2016-11-29/d03
    ctmDir = "/opt/project/data/cmaq/"  ## base directory for the CCTM inputs and outputs

    ## same convention for the CMAQ output as for the MCIP output, except with ctmDir
    wrfDir = "/opt/project/data/runs/aust-test"  ## directory containing wrfout_* files
    ## convention for WRF output, is wrfDir/2016112900/wrfout_d03_*
    geoDir = "/opt/project/templates/aust-test/"  ## directory containing geo_em.* files
    inputCAMSFile = "/opt/project/data/inputs/levtype_pl.nc"
    sufadj = "output_newMet"  # this is added by sougol to match the name of the folder created by running adj executable.

    domains = ["d01"]  ## which domains should be run?
    run = "openmethane"  ## name of the simulation, appears in some filenames (keep this *short* - longer)
    mcipSuffix = ["2"]
    startDate = datetime.datetime(2024, 1, 1, 0, 0, 0)  ## this is the START of the first day
    endDate = datetime.datetime(2024, 1, 1, 0, 0)  ## this is the START of the last day
    nhoursPerRun = 24  ## number of hours to run at a time (24 means run a whole day at once)
    printFreqHours = 1  ## frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly

    ## preparation
    mech = "CH4only"  ## name of chemical mechanism to appear in filenames
    mechCMAQ = "CH4only"  ## name of chemical mechanism given to CMAQ (should be one of: cb05e51_ae6_aq, cb05mp51_ae6_aq, cb05tucl_ae6_aq, cb05tump_ae6_aq, racm2_ae6_aq, saprc07tb_ae6_aq, saprc07tc_ae6_aq, saprc07tic_ae6i_aq, saprc07tic_ae6i_aqkmti)

    prepareICandBC = True  # prepare the initial and boundary conditions from global CAMS output
    prepareRunScripts = True  # prepare the run scripts

    ## MCIP options
    add_qsnow = False  ## add the 'QSNOW' variable to the WRFOUT files before running MCIP

    forceUpdateMcip = False  # force the update of the MCIP files
    forceUpdateICandBC = (
        True  # force an update of the initial and boundary conditions from global MOZART output
    )
    forceUpdateRunScripts = True  # force an update to the run scripts

    scenarioTag = "220701_10km"  # scenario tag (for MCIP). 16-character maximum
    mapProjName = "LamCon_34S_150E"  # Map projection name (for MCIP). 16-character maximum
    gridName = "openmethane"  # Grid name (for MCIP). 16-character maximum

    doCompress = True  ## compress the output from netCDF3 to netCDF4 during the CMAQ run
    compressScript = "/home/563/ns0890/runCMAQ/Melb_Sch01/find_and_compress_netcdf3_to_netcdf4"  ## script to find and compress netCDF3 to netCDF4

    ## This is a dictionary with paths to each of the
    ## run-scripts. Elements of the dictionary should themselves be
    ## dictionaries, with the key 'path' and the value being the path
    ## to that file. The keys of the 'scripts' dictionary should be as follow:
    # mcipRun - MCIP run script
    # bconRun - BCON run script
    # iconRun - ICON run script
    # cctmRun - CCTM run script
    # cmaqRun - main CMAQ run script
    scripts = {
        "mcipRun": {"path": f"{templateDir}/run.mcip"},
        "bconRun": {"path": f"{templateDir}/run.bcon"},
        "iconRun": {"path": f"{templateDir}/run.icon"},
        "cctmRun": {"path": f"{templateDir}/run.cctm"},
        "cmaqRun": {"path": f"{templateDir}/runCMAQ.sh"},
    }

    ################ MOST USER INPUT SHOULD BE ABOVE HERE ###################

    ## dfine date range
    ndates = (endDate - startDate).days + 1
    dates = [startDate + datetime.timedelta(days=d) for d in range(ndates)]

    ## read in the template run-scripts
    scripts = helper_funcs.loadScripts(Scripts=scripts)

    ## create output destinations, if need be:
    print(
        "Check that input meteorology files are provided and create output destinations (if need be)"
    )
    mcipOuputFound = checkWrfMcipDomainSizes.checkInputMetAndOutputFolders(
        ctmDir, metDir, dates, domains
    )
    print("\t... done")

    if (not mcipOuputFound) or forceUpdateMcip:
        runMCIP.runMCIP(
            dates=dates,
            domains=domains,
            metDir=metDir,
            wrfDir=wrfDir,
            geoDir=geoDir,
            ProgDir=MCIPdir,
            APPL=scenarioTag,
            CoordName=mapProjName,
            GridName=gridName,
            scripts=scripts,
            compressWithNco=True,
            fix_simulation_start_date=True,
            fix_truelat2=False,
            truelat2=None,
            wrfRunName=None,
            doArchiveWrf=False,
            add_qsnow=add_qsnow,
        )

    ## extract some parameters about the MCIP setup
    cctmExec = "ADJOINT_FWD"
    CoordNames, GridNames, APPL = checkWrfMcipDomainSizes.getMcipGridNames(metDir, dates, domains)

    if prepareICandBC:
        ## prepare the template boundary condition concentration files
        ## from profiles using BCON
        templateBconFiles = configureRunScripts.prepareTemplateBconFiles(
            date=dates[0],
            domains=domains,
            ctmDir=ctmDir,
            metDir=metDir,
            CMAQdir=CMAQdir,
            CFG=run,
            mech=mechCMAQ,
            GridNames=GridNames,
            mcipsuffix=APPL,
            scripts=scripts,
            forceUpdate=forceUpdateICandBC,
        )
        ## prepare the template initial condition concentration files
        ## from profiles using ICON
        templateIconFiles = configureRunScripts.prepareTemplateIconFiles(
            date=dates[0],
            domains=domains,
            ctmDir=ctmDir,
            metDir=metDir,
            CMAQdir=CMAQdir,
            CFG=run,
            mech=mechCMAQ,
            GridNames=GridNames,
            mcipsuffix=APPL,
            scripts=scripts,
            forceUpdate=forceUpdateICandBC,
        )
        ## use the template initial and boundary condition concentration
        ## files and populate them with values from MOZART output
        interpolateFromCAMS.interpolateFromCAMSToCmaqGrid(
            dates,
            domains,
            mech,
            inputCAMSFile,
            templateIconFiles,
            templateBconFiles,
            metDir,
            ctmDir,
            GridNames,
            mcipSuffix,
            forceUpdateICandBC,
            bias_correct=(1.838 - 1.771),
        )

    if prepareRunScripts:
        # print("gfcbcjucrhcnrcbrbcnrchnrchnrhcrhcnricrhncruicjnrdfic")
        print("Prepare ICON, BCON and CCTM run scripts")
        ## prepare the scripts for CCTM
        configureRunScripts.prepareCctmRunScripts(
            dates=dates,
            domains=domains,
            ctmDir=ctmDir,
            metDir=metDir,
            CMAQdir=CMAQdir,
            CFG=run,
            mech=mech,
            mechCMAQ=mechCMAQ,
            GridNames=GridNames,
            mcipsuffix=APPL,
            scripts=scripts,
            EXEC=cctmExec,
            SZpath=ctmDir,
            nhours=nhoursPerRun,
            printFreqHours=printFreqHours,
            forceUpdate=forceUpdateRunScripts,
        )  ## prepare the scripts for BCON
        configureRunScripts.prepareBconRunScripts(
            sufadjname=sufadj,
            dates=dates,
            domains=domains,
            ctmDir=ctmDir,
            metDir=metDir,
            CMAQdir=CMAQdir,
            CFG=run,
            mech=mech,
            mechCMAQ=mechCMAQ,
            GridNames=GridNames,
            mcipsuffix=APPL,
            scripts=scripts,
            forceUpdate=forceUpdateRunScripts,
        )
        ## prepare the main run script
        configureRunScripts.prepareMainRunScript(
            dates=dates,
            domains=domains,
            ctmDir=ctmDir,
            CMAQdir=CMAQdir,
            scripts=scripts,
            doCompress=doCompress,
            compressScript=compressScript,
            run=run,
            forceUpdate=forceUpdateRunScripts,
        )
    ##


if __name__ == "__main__":
    main()
