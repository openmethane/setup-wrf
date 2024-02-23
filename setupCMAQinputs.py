## Top level run script for the preparation phase
#
# This is the top-level script that sets up the CMAQ inputs. Most of
# the detail and functionality is found in a series of accompanying
# files. Tasks performed:
#  - create output destinations (if need be)
#  - check the latitudes and longitudes of the WRF and MCIP grids against one another
#  - prepare the JPROC files (precomuted photochemical rate constants)
#  - prepare the MEGAN emissions (biogenic)
#  - merge the anthropogenic emissions, GFAS fire emissions and biogenic emissions
#  - prepare the initial and boundary conditions from global CTM output
#  - prepare run scripts for ICON, BCON and CCTM programs within the CMAQ  bundle
#
# Author: Jeremy Silver (jeremy.silver@unimelb.edu.au)
# Date: 2016-11-04



 
## load standard python libraries (other are imported by the accompanying scripts)
import datetime
## custom python libraries (really these are just the accompanying files)
import anthropEmis
import helper_funcs
import prepareMEGAN
import prepareJprocFiles
import prepareFireEmis
import checkWrfMcipDomainSizes
import interpolateFromCAMS
import configureRunScripts
import surfzonegeo
import runMCIP

## The main routine controlling the CMAQ preparation phase
#
#Most of the important variables are set here. These are:
#- CMAQdir:  base directory for the CMAQ model
#- MCIPdir:  directory containing the MCIP executable
#- photDir:  path to the photolysis data files (available with the CMAQ benchmark data set)
#- MEGANdir:  base directory for the MEGAN suite
#- prepMEGANdir:  base directory for the prepmegan4cmaq suite
#- LaiPftEmfacDir: folder containing leaf area index, plant functional type and emission factor maps required for MEGAN
#- wrfDirForMegan: Directory containing the wrfinp* files
#- GFASdir: directory containing the GFAS data
#- ANTHROPdir:  folder containing the wrfchemi_* anthropogenic emission files
#- templateDir:  folder containing the template run scripts
#- metDir: base directory for the MCIP output
#- ctmDir: base directory for the CCTM inputs and outputs
#- wrfDir: directory containing wrfout_* files
#- geoDir: directory containing geo_em.* files
#- mozartSpecIndex: speciation file, mapping MOZART to CMAQ species
#- gfasSpecIndexFile: speciation file, mapping GFAS to CMAQ species
#- wrfchemSpecIndexFile:  speciation file, mapping WRFCHEMI to CMAQ species
#- tempDir: directory for temporary files
#- inputMozartFile: Output from MOZART to use for boundary and initial conditions
#- cmaqVersionCode: abbreviated CMAQ number
#- coastlineShapefiles: a list of shapefiles describing coastlines for use in the surf-zone calculates. One per entry per domain
#- cmaqEnvScript: path to the (bash) shell script that sets all of the run-time variables for CMAQ (e.g. LD_LIBRARY_PATH, module load <name>, etc.)
#- wrfDate: the date in the WRF filenames
#- GFASfile:  the file (within directory GFASdir) containing GFAS fire emission data
#- domains: list of which domains should be run?
#- run: name of the simulation, appears in some filenames (keep this *short* - longer)
#- startDate: this is the START of the first day
#- endDate: this is the START of the last day
#- nhoursPerRun: number of hours to run at a time (24 means run a whole day at once)
#- printFreqHours: frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly
#- mech: name of chemical mechanism to appear in filenames
#- mechMEGAN: name of chemical mechanism given to MEGAN (should be one of: RADM2, RACM, CBMZ, CB05, CB6, SOAX, SAPRC99, SAPRC99Q, SAPRC99X)
#- mechCMAQ: name of chemical mechanism given to CMAQ (should be one of: cb05e51_ae6_aq, cb05mp51_ae6_aq, cb05tucl_ae6_aq, cb05tump_ae6_aq, racm2_ae6_aq, saprc07tb_ae6_aq, saprc07tc_ae6_aq, saprc07tic_ae6i_aq, saprc07tic_ae6i_aqkmti)
#- addMegan: combined emissions include MEGAN biogenic 
#- addFires: combined emissions include GFAS fires
#- prepareEmis: prepare the emission files
#- prepareICandBC: prepare the initial and boundary conditions from global MOZART output
#- prepareRunScripts: prepare the run scripts
#- forceUpdateMcip: force the update of the MCIP files
#- forceUpdateJproc: force the update of the JPROC (photolysis rate constant) files
#- forceUpdateSZ: force the update of the surfzone files
#- forceUpdateMegan: force the update of MEGAN emission files
#- forceUpdateFires: force the update of GFAS emission files
#- forceUpdateMerger: force the merging of anthropogenic, biogenic and fire emissions
#- forceUpdateICandBC: force an update of the initial and boundary conditions from global MOZART output
#- forceUpdateRunScripts: force an update to the run scripts
#- scenarioTag: scenario tag (for MCIP). 16-character maximum
#- mapProjName: Map projection name (for MCIP). 16-character maximum
#- gridName: Grid name (for MCIP). 16-character maximum
#- doCompress: compress the output from netCDF3 to netCDF4 during the CMAQ run
#- compressScript: script to find and compress netCDF3 to netCDF4
#- scripts: This is a dictionary with paths to each of the run-scripts. Elements of the dictionary should themselves be dictionaries, with the key 'path' and the value being the path to that file. The keys of the 'scripts' dictionary should be as follow: mcipRun: MCIP run script; bconRun: BCON run script; iconRun: ICON run script; cctmRun: CCTM run script; jprocRun: JPROC run script; prepMegan4Cmaq: prepmegan4cmaq run script; megansetcase: MEGAN setcase;csh file; txt2ioapi: MEGAN TXT2IOAPI run script; met2mgn: MEGAN MET2MGN run script; emproc: MEGAN EMPROC run script; mgn2mech: MEGAN MGN2MECH run script; cmaqRun: main CMAQ run script; pbsRun: PBS submission script.
#- copyInputsFromPreviousSimulation copy some/all of the inputs from a previous run
#- oldCtmDir: which directory to copy from (this is the base directory)
#- oldRun: the 'run' variable from the previous simulation
#- copyEFMAPS: copy the EFMAPS files?
#- copyLAIS: copy the LAIS files?
#- copyPFTS: copy the PFTS files
#- copySURFZONE: copy the surfzone files?
#- copyJTABLE: copy the JTABLE files?
#- copyTemplateIC: copy the template IC files
#- copyTemplateBC: copy the template BC files
#- copyBCON: copy the daily BC files
#- copyICON: copy the daily IC files
#- copyFIREEMIS: copy the fire emissions
#- copyMEGANEMIS: copy the megan emissions
#- copyMERGEDEMIS: copy the merged emissions
#- linkInsteadOfCopy: if 'True', symbolic links are made rather than copies
def main():

    
    ################ MOST USER INPUT SHOULD BE BELOW HERE ###################

    ## directories    
    CMAQdir = "/home/563/sa6589/CMAQv5.0.2_notpollen/" ## base directory for the CMAQ model
    MCIPdir = "/home/563/sa6589/CMAQv5.0.2_notpollen/scripts/mcip/src" ## directory containing the MCIP executable
    photDir = "/scratch/q90/sa6589/test_Sougol/shared_Sougol/raw/phot" ## path to the photolysis data files (available with the CMAQ benchmark data set)
    MEGANdir = "/home/563/sa6589/programs/MEGANv2.10/" ## base directory for the MEGAN suite
    # prepMEGANdir = '/short/lp86/jds563/code/prepmegan4cmaq_2014-06-02' ## base directory for the prepmegan4cmaq suite
    prepMEGANdir = "/home/563/ns0890/programs/prepmegan4cmaq_2014-06-02/"
    # LaiPftEmfacDir = '/short/lp86/jds563/data/MEGAN/WSU' ## folder containing leaf area index, plant functional type and emission factor maps required for MEGAN
    # LaiPftEmfacDir = '/short/lp86/sru563/Megan/data/global/'
    LaiPftEmfacDir = '/scratch/lp86/ns0890/data/globalMeganData/'  
    wrfDirForMegan = "/scratch/lp86/ns0890/WRF/Melb_Sch01/"
    
    ##Fix me 
    GFASdir = "/scratch/lp86/ns0890/data/CTM/Melb_Sch01/" ## directory containing the GFAS data
    ANTHROPdir = "/scratch/lp86/ns0890/data/CTM/Melb_Sch01/Antropogenic/" ## folder containing the regridded EDGAR anthropogenic emission files
    
    templateDir = "/home/563/pjr563/openmethane-beta/setup_wrf/templateRunScripts" ## folder containing the template run scripts
    metDir = "/scratch/q90/pjr563/openmethane-beta/mcip/" ## base directory for the MCIP output
    ## convention for MCIP output is that we have data organised by day and domain, eg metDir/2016-11-29/d03
    ctmDir = "/scratch/q90/pjr563/openmethane-beta/cmaq/" ## base directory for the CCTM inputs and outputs
    ##Melb_Sch01ctmDir = '/short/lp86/ns0890/data/CTM/Melb_Sch01/'
    
    ## same convention for the CMAQ output as for the MCIP output, except with ctmDir
    wrfDir = "/scratch/q90/pjr563/openmethane-beta/wrf/aust10km" ## directory containing wrfout_* files
    ## convention for WRF output, is wrfDir/2016112900/wrfout_d03_*
    geoDir = "/home/563/pjr563/openmethane-beta/setup_wrf/templates/aust10km/" ## directory containing geo_em.* files
    #mozartSpecIndex = '/home/563/ns0890/runCMAQ/Melb_Sch01/speciesTables/species_table_CAMCHEM_CBM05.txt' ## speciation file, mapping MOZART to CMAQ (CBM05) species
    specTableFile='/scratch/q90/sa6589/test_Sougol/shared_Sougol/Melb_Sch01/speciesTables/species_table_WACCM.txt'
    gfasSpecIndexFile = '/scratch/q90/sa6589/test_Sougol/shared_Sougol/Melb_Sch01/speciesTables/species_table_GFAS_CBM05.txt' ## speciation file, mapping GFAS to CMAQ (CBM05) species
    #wrfchemSpecIndexFile = '/home/563/ns0890/runCMAQ/Melb_Sch01/speciesTables/species_table_WRFCHEM_CBM05.txt' ## speciation file, mapping WRFCHEMI to CMAQ (CBM05) species
    tempDir = '/scratch/q90/pjr563/openmethane-beta/tmp' ## directory for temporary files
    inputCAMSFile = "/scratch/q90/pjr563/tmp/levtype_pl.nc"
    cmaqVersionCode = 'CH4only' ##'D502a' ## abbreviated CMAQ number
    coastlineShapefiles = ["/scratch/lp86/ns0890/data/landuse/gshhg/GSHHS_shp/c/GSHHS_c_L1.shp",
                           "/scratch/lp86/ns0890/data/landuse/gshhg/GSHHS_shp/l/GSHHS_l_L1.shp",
                           "/scratch/lp86/ns0890/data/landuse/gshhg/GSHHS_shp/i/GSHHS_i_L1.shp",
                           "/scratch/lp86/ns0890/data/landuse/gshhg/GSHHS_shp/i/GSHHS_i_L1.shp"] ## a list of shapefiles describing coastlines for use in the surf-zone calculates. One per entry per domain
    cmaqEnvScript = '/home/563/pjr563/openmethane-beta/setup_wrf/load_cmaq_env.sh' ## path to the (bash) shell script that sets all of the run-time variables for CMAQ (e.g. LD_LIBRARY_PATH, module load <name>, etc.)

    wrfDate = datetime.datetime(2022,7,1,0,0,0) ## this is the date in the WRF filenames but appears unused
    sufadj="output_newMet"  #this is added by sougol to match the name of the folder created by running adj executable.
    GFASfile = "GFAS_Australia.nc" ## the file (within directory GFASdir) containing GFAS fire emission data

    domains = ['d01'] ## which domains should be run?
    run = 'openmethane' ## name of the simulation, appears in some filenames (keep this *short* - longer)
    mcipSuffix = ['2']
    startDate = datetime.datetime(2022,7,1, 0, 0, 0) ## this is the START of the first day
    endDate = datetime.datetime(2022,7,31, 0, 0) ## this is the START of the last day
    nhoursPerRun = 24 ## number of hours to run at a time (24 means run a whole day at once)
    printFreqHours = 1 ## frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly

    ## preparation
    mech       = 'CH4only' ## name of chemical mechanism to appear in filenames
    mech       = 'CH4only' ## name of chemical mechanism to appear in filenames
    mechMEGAN  = 'CB05' # name of chemical mechanism given to MEGAN (should be one of: RADM2, RACM, CBMZ, CB05, CB6, SOAX, SAPRC99, SAPRC99Q, SAPRC99X)
    
    mechCMAQ   = 'CH4only' ## name of chemical mechanism given to CMAQ (should be one of: cb05e51_ae6_aq, cb05mp51_ae6_aq, cb05tucl_ae6_aq, cb05tump_ae6_aq, racm2_ae6_aq, saprc07tb_ae6_aq, saprc07tc_ae6_aq, saprc07tic_ae6i_aq, saprc07tic_ae6i_aqkmti)

    addMegan   = False # combined emissions include MEGAN biogenic 
    addFires   = False # combined emissions include GFAS fires
    prepareEmis = False # prepare the emission files
    prepareICandBC = True # prepare the initial and boundary conditions from global CAMS output
    prepareRunScripts = True # prepare the run scripts

    ## MCIP options
    add_qsnow = False ## add the 'QSNOW' variable to the WRFOUT files before running MCIP

    forceUpdateMcip = False # force the update of the MCIP files
    forceUpdateJproc = False  # force the update of the JPROC (photolysis rate constant) files
    forceUpdateSZ = False # force the update of the surfzone files
    forceUpdateMegan = False # force the update of MEGAN emission files
    forceUpdateFires = False # force the update of GFAS emission files
    forceUpdateMerger = False # force the merging of anthropogenic, biogenic and fire emissions
    forceUpdateICandBC = True # force an update of the initial and boundary conditions from global MOZART output
    forceUpdateRunScripts = True # force an update to the run scripts

    scenarioTag = '220701_10km'         # scenario tag (for MCIP). 16-character maximum
    mapProjName = 'LamCon_34S_150E'    # Map projection name (for MCIP). 16-character maximum
    gridName    = 'openmethane'        # Grid name (for MCIP). 16-character maximum
    
    doCompress = True ## compress the output from netCDF3 to netCDF4 during the CMAQ run
    compressScript = '/home/563/ns0890/runCMAQ/Melb_Sch01/find_and_compress_netcdf3_to_netcdf4' ## script to find and compress netCDF3 to netCDF4

    ## This is a dictionary with paths to each of the
    ## run-scripts. Elements of the dictionary should themselves be
    ## dictionaries, with the key 'path' and the value being the path
    ## to that file. The keys of the 'scripts' dictionary should be as follow:
    # mcipRun - MCIP run script
    # bconRun - BCON run script
    # iconRun - ICON run script
    # cctmRun - CCTM run script
    # jprocRun - JPROC run script
    # prepMegan4Cmaq - prepmegan4cmaq run script
    # megansetcase - MEGAN setcase.csh file
    # txt2ioapi - MEGAN TXT2IOAPI run script
    # met2mgn - MEGAN MET2MGN run script
    # emproc - MEGAN EMPROC run script
    # mgn2mech - MEGAN MGN2MECH run script
    # cmaqRun - main CMAQ run script
    # pbsRun - PBS submission script
    scripts = {'mcipRun':{'path': '{}/run.mcip'.format(templateDir)},
               'bconRun': {'path': '{}/run.bcon'.format(templateDir)},
               'iconRun': {'path': '{}/run.icon'.format(templateDir)},
               'cctmRun': {'path': '{}/run.cctm'.format(templateDir)},
               'jprocRun': {'path': '{}/run.jproc'.format(templateDir)}, 
               'prepMegan4Cmaq': {'path': '{}/prepmegan4cmaq.inp'.format(templateDir)},
               'megansetcase': {'path': '{}/setcase.csh'.format(templateDir)},
               'txt2ioapi': {'path': '{}/run.txt2ioapi.v210.csh'.format(templateDir)}, 
               'met2mgn': {'path': '{}/run.met2mgn.v210.csh'.format(templateDir)}, 
               'emproc': {'path': '{}/run.emproc.v210.csh'.format(templateDir)}, 
               'mgn2mech': {'path': '{}/run.mgn2mech.v210.csh'.format(templateDir)},
               'cmaqRun': {'path': '{}/runCMAQ.sh'.format(templateDir)},
               'pbsRun': {'path': '{}/PBS_CMAQ_job.sh'.format(templateDir)}}

    copyInputsFromPreviousSimulation = False ## copy some/all of the inputs from a previous run
    oldCtmDir = '' ## which directory to copy from (this is the base directory)
    oldRun = '' ## the 'run' variable from the previous simulation
    copyEFMAPS = False ## copy the EFMAPS files?
    copyLAIS = False ## copy the LAIS files?
    copyPFTS = False ## copy the PFTS files
    copySURFZONE = True ## copy the surfzone files?
    copyJTABLE = True ## copy the JTABLE files?
    copyTemplateIC = False ## copy the template IC files
    copyTemplateBC = False ## copy the template BC files
    copyBCON = False ## copy the daily BC files
    copyICON = False ## copy the daily IC files
    copyFIREEMIS = False ## copy the fire emissions
    copyMEGANEMIS = False ## copy the megan emissions
    copyMERGEDEMIS = False ## copy the merged emissions
    linkInsteadOfCopy = False ## if 'True', symbolic links are made rather than copies

    ################ MO,ST USER INPUT SHOULD BE ABOVE HERE ###################

    ## dfine date range
    ndates = (endDate - startDate).days + 1
    dates = [startDate + datetime.timedelta(days = d) for d in range(ndates)]

    ## read in the template run-scripts
    scripts = helper_funcs.loadScripts(Scripts = scripts)

    ndomains = len(domains)

    ## create output destinations, if need be:
    print("Check that input meteorology files are provided and create output destinations (if need be)")
    mcipOuputFound = checkWrfMcipDomainSizes.checkInputMetAndOutputFolders(ctmDir,metDir,dates,domains)
    print("\t... done")

    if (not mcipOuputFound) or forceUpdateMcip:
        runMCIP.runMCIP(dates = dates, domains = domains, metDir = metDir, wrfDir = wrfDir, ## wrfDate = wrfDate, 
                        geoDir = geoDir, ProgDir = MCIPdir, APPL = scenarioTag, CoordName = mapProjName, GridName = gridName, scripts = scripts,
                compressWithNco = True, ## fix_prec_acc_dt = False, 
                        fix_simulation_start_date = True,
                        fix_truelat2 = False, truelat2 = None, wrfRunName = None, doArchiveWrf = False, add_qsnow = add_qsnow)

    if prepareICandBC:
        ## prepare the template boundary condition concentration files
        ## from profiles using BCON
        templateBconFiles = configureRunScripts.prepareTemplateBconFiles(date = dates[0], domains = domains, ctmDir = ctmDir, metDir = metDir, CMAQdir = CMAQdir, CFG = run, mech  = mechCMAQ, GridNames = GridNames, mcipsuffix = APPL, scripts = scripts, forceUpdate = forceUpdateICandBC)
        ## prepare the template initial condition concentration files
        ## from profiles using ICON
        templateIconFiles = configureRunScripts.prepareTemplateIconFiles(date = dates[0], domains = domains, ctmDir = ctmDir, metDir = metDir, CMAQdir = CMAQdir, CFG = run, mech  = mechCMAQ, GridNames = GridNames, mcipsuffix = APPL, scripts = scripts, forceUpdate = forceUpdateICandBC)
        ## use the template initial and boundary condition concentration
        ## files and populate them with values from MOZART output
        interpolateFromCAMS.interpolateFromCAMSToCmaqGrid(dates, domains, mech,\
                                                          inputCAMSFile, templateIconFiles,\
                                                          templateBconFiles, specTableFile,\
                                                          metDir, ctmDir,\
                                                          GridNames, mcipSuffix,\
                                                          forceUpdateICandBC, bias_correct=(1.838-1.771))

    if prepareRunScripts:
        #print("gfcbcjucrhcnrcbrbcnrchnrchnrhcrhcnricrhncruicjnrdfic")
        print("Prepare ICON, BCON and CCTM run scripts")
        ## prepare the scripts for CCTM
        configureRunScripts.prepareCctmRunScripts(sufadjname=sufadj, dates = dates, domains = domains, ctmDir = ctmDir, metDir = metDir, CMAQdir = CMAQdir, CFG = run, mech = mech, mechCMAQ = mechCMAQ, GridNames = GridNames, mcipsuffix = APPL, scripts = scripts, EXEC = cctmExec, SZpath = ctmDir, nhours = nhoursPerRun, printFreqHours = printFreqHours, forceUpdate = forceUpdateRunScripts)      ## prepare the scripts for BCON
        configureRunScripts.prepareBconRunScripts(sufadjname=sufadj, dates = dates, domains = domains, ctmDir = ctmDir, metDir = metDir, CMAQdir = CMAQdir, CFG = run, mech = mech, mechCMAQ = mechCMAQ, GridNames = GridNames, mcipsuffix = APPL, scripts = scripts, EXEC = cctmExec, forceUpdate = forceUpdateRunScripts)
        ## prepare the main run script
        configureRunScripts.prepareMainRunScript(dates = dates, domains = domains, ctmDir = ctmDir, CMAQdir = CMAQdir, scripts = scripts, doCompress = doCompress, compressScript = compressScript, run = run, forceUpdate = forceUpdateRunScripts)
    ##
    return

if __name__ == "__main__":
    main()
