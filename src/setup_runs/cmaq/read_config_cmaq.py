import datetime

from attrs import define, field

@define
class CMAQConfig :
    CMAQdir : str
    """ base directory for the CMAQ model """
    MCIPdir : str
    """directory containing the MCIP executable"""
    templateDir : str
    """folder containing the template run scripts"""
    metDir : str
    """base directory for the MCIP output. 
    convention for MCIP output is that we have data organised by day and domain, eg metDir/2016-11-29/d03"""
    ctmDir : str
    """base directory for the CCTM inputs and outputs. same convention for the 
    CMAQ output as for the MCIP output, except with ctmDir"""
    wrfDir : str
    """directory containing wrfout_* files, convention for WRF output, is wrfDir/2016112900/wrfout_d03_*"""
    geoDir : str
    """directory containing geo_em.* files"""
    inputCAMSFile : str
    """Filepath to CAMS file."""
    sufadj : str
    """this is added by sougol to match the name of the folder created by running adj executable."""
    domains : list[str]
    """which domains should be run?"""
    run : str
    """name of the simulation, appears in some filenames (keep this *short* - longer)"""
    startDate : datetime.datetime
    """this is the START of the first day"""
    endDate : datetime.datetime
    """this is the START of the last day"""
    # TODO: Check if int is the right type. Perhaps time units between full hours are supported.
    nhoursPerRun : int
    """number of hours to run at a time (24 means run a whole day at once)"""
    printFreqHours : int
    """frequency of the CMAQ output (1 means hourly output) - so far it is not set up to run for sub-hourly"""
    mech : str
    """name of chemical mechanism to appear in filenames"""
    mechCMAQ : str
    """name of chemical mechanism given to CMAQ (should be one of: cb05e51_ae6_aq, cb05mp51_ae6_aq,
    cb05tucl_ae6_aq, cb05tump_ae6_aq, racm2_ae6_aq, saprc07tb_ae6_aq, saprc07tc_ae6_aq,
    saprc07tic_ae6i_aq, saprc07tic_ae6i_aqkmti)"""
    prepareICandBC : bool
    """prepare the initial and boundary conditions from global CAMS output"""
    prepareRunScripts : bool
    """prepare the run scripts"""
    add_qsnow : bool
    """MCIP option: add the 'QSNOW' variable to the WRFOUT files before running MCIP"""
    forceUpdateMcip : bool
    """MCIP option: force the update of the MCIP files"""
    forceUpdateICandBC : tuple[bool]
    """MCIP option: force an update of the initial and boundary conditions from global MOZART output"""
    forceUpdateRunScripts : bool
    """MCIP option: force an update to the run scripts"""
    scenarioTag : list[str]
    """MCIP option: scenario tag. 16-character maximum"""
    mapProjName : list[str]
    """MCIP option: Map projection name. 16-character maximum"""
    gridName : list[str]
    """MCIP option: Grid name. 16-character maximum"""
    doCompress : str
    """compress the output from netCDF3 to netCDF4 during the CMAQ run"""
    compressScript : str
    """script to find and compress netCDF3 to netCDF4"""
    scripts : dict[str, dict[str, str]]
    """This is a dictionary with paths to each of the run-scripts. Elements of the dictionary should themselves be
    dictionaries, with the key 'path' and the value being the path to that file. The keys of the 'scripts' 
    dictionary should be as follow:
    mcipRun - MCIP run script
    bconRun - BCON run script
    iconRun - ICON run script
    cctmRun - CCTM run script
    cmaqRun - main CMAQ run script"""
    cctmExec : str
    # TODO: Add description for cctmExec?
    CAMSToCmaqBiasCorrect : float
    # TODO: Add description for CAMSToCmaqBiasCorrect?


def load_cmaq_config(config):
    return CMAQConfig(**config)