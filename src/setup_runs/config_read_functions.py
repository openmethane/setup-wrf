import os
import sys
import json
import re
from typing import Tuple
import datetime
import pytz
# import attr
from attrs import define, field


def boolean_converter(value) :
    truevals = ['true', '1', 't', 'y', 'yes']
    falsevals = ['false', '0', 'f', 'n', 'no']
    boolvals = truevals + falsevals

    assert (value.lower() in boolvals), f'Key {value} not a recognised boolean value'

    return (value.lower() in truevals)


@define
class WRFConfig :
    project_root: str
    """overall base directory for project"""
    setup_root: str
    """" base dir for set up scripts """
    run_name: str
    """Project name """
    target: str
    """Target environment for running tasks"""
    start_date: str
    """start first simulation, "%Y-%m-%d %H:%M:%S %Z" or just "%Y-%m-%d %H:%M:%S" for UTC"""
    end_date: str
    """The end time of the last simulation (same format as above)"""
    # FIXME: this hasn't been fully implemented yet (only working for 'false')
    restart: str = field(converter=boolean_converter)
    """Is this a restart run? (bool -> true/false, yes/no)"""
    num_hours_per_run: int
    """Number of hours of simulation of each run (excluding spin-up)"""
    num_hours_spin_up: int
    """Number of hours of spin-up simulation of each run"""
    run_as_one_job: str = field(converter=boolean_converter)
    """submit run as one job (if false, each run needs to get through the queue separately)"""
    submit_wrf_now: str = field(converter=boolean_converter)
    """"""
    submit_wps_component: str = field(converter=boolean_converter)
    """Submit the WRF runs at the end of the script? (bool -> true/false, yes/no)
    FIXME: this hasn't been fully implemented yet (only working for 'false')"""
    environment_variables_for_substitutions: str
    """shell environment variables to be used for substitutions in this script"""
    run_dir: str
    """top-level directory for the WRF and WPS outputs"""
    run_script_template: str
    """filename of the template run-script"""
    cleanup_script_template: str
    """filename of the template script for clean-up duties"""
    main_script_template: str
    """filename of the template script to coordinate the process"""
    check_wrfout_in_background_script: str
    """"""
    only_edit_namelists: str = field(converter=boolean_converter)
    """should the only task performed by the python script be to edit the WRF namelists and the shell 
    scripts (the daily run-script, the daily clean-up script and the main coordination script)"""
    use_high_res_sst_data: str = field(converter=boolean_converter)
    """should we use the RTG high resolution SSTs?"""
    wps_dir: str
    """the top-level WPS directory"""
    wrf_dir: str
    """the top-level directory containing the WRF executables and data-tables"""
    nml_dir: str
    """the directory containining the run specific configuration (the directory with template namelists)"""
    target_dir: str
    """the directory containing the target-specific configuration"""
    scripts_to_copy_from_nml_dir: str
    """scripts to copy from directory ${nml_dir} to each day"""
    scripts_to_copy_from_target_dir: str
    """scripts to copy from directory targets/${target} to each day"""
    metem_dir: str
    """output location for the met_em files"""
    namelist_wps: str
    """template namelist for WPS"""
    namelist_wrf: str
    """template namelist for WRF"""
    geog_data_path: str
    """path to the geography data files"""
    geogrid_tbl: str
    """path to the GEOGRID.TBL file"""
    geogrid_exe: str
    """path to the geogrid.exe program"""
    ungrib_exe: str
    """path to the ungrib.exe program"""
    metgrid_tbl: str
    """path to the METGRID.TBL file"""
    metgrid_exe: str
    """path to the metgrid.exe program"""
    linkgrib_script: str
    """path to the link_grib.csh script"""
    wrf_exe: str
    """path to the wrf.exe program"""
    real_exe: str
    """path to the real.exe program"""
    delete_metem_files: str = field(converter=boolean_converter)
    """delete met_em files once they have been used"""
    analysis_source: str
    """analysis source - can be ERAI or FNL"""
    orcid: str
    """if analysis_source is "FNL", you will need a login for CISL/rda.ucar.edu"""
    rda_ucar_edu_api_token: str
    """"""
    regional_subset_of_grib_data: str = field(converter=boolean_converter)
    """if analysis_source is "FNL", it's a good idea to take a subset of the grib2 files"""
    sst_monthly_dir: str
    """directory containing monthly SST files"""
    sst_daily_dir: str
    """directory containing daily SST files"""
    sst_monthly_pattern: str
    """pattern for matching monthly SST files (date-time substitutions recognised)"""
    sst_daily_pattern: str
    """pattern for matching daily SST files (date-time substitutions recognised)"""
    sst_vtable: str
    """VTable file for the SST GRIB files"""
    analysis_pattern_upper: str
    """pattern for matching the full-atmosphere analysis files (date-time substitutions recognised as well as shell wildcards)"""
    analysis_pattern_surface: str
    """pattern for matching the surface-level analysis files (date-time substitutions recognised as well as shell wildcards)"""
    analysis_vtable: str
    """VTable file for the SST analysis files"""
    wrf_run_dir: str
    """directory containing WRF input tables and data-files"""
    wrf_run_tables_pattern: str
    """pattern to match to get the WRF input tables and data-files (within the folder ${wrf_run_dir}"""


def read_config_file(configFile: str) -> str :
    """
    Reads and returns the content of a configuration file.

    Parameters
    ----------
    configFile
        The path to the configuration file.

    Returns
    -------
        The content of the configuration file.

    Raises
    ------
    AssertionError
        If the configuration file does not exist.
    """

    assert os.path.exists(
        configFile
    ), f"No configuration file was found at {configFile}"

    try :
        with open(configFile, 'rt') as f :
            input_str = f.read()
        return input_str
    except Exception as e :
        print("Problem reading in configuration file")
        print(e)
        sys.exit()


def parse_config(input_str: str) -> dict :
    """
    Parses the input string containing configuration data and returns a JSON object.

    Parameters
    ----------
    input_str
        The input string containing configuration data.

    Returns
    -------
        The parsed configuration data.

    Raises
    ------
    Exception
        If there is an issue with parsing the configuration data.
    """

    try :
        ## strip out the comments
        input_str = re.sub(r'#.*\n', '\n', input_str)
        return json.loads(input_str)
    except Exception as e :
        print("Problem parsing in configuration file")
        print(e)
        sys.exit()


def add_environment_variables(config: dict, environmental_variables: dict) -> dict :
    """
    Adds environment variables to the configuration that may be needed for substitutions.

    Parameters
    ----------
    config
        The configuration dictionary.

    Returns
    -------
        The updated configuration dictionary with added environment variables.
    """
    envVarsToInclude = config["environment_variables_for_substitutions"].split(',')
    for envVarToInclude in envVarsToInclude :
        if envVarToInclude in list(environmental_variables.keys()) :
            config[envVarToInclude] = environmental_variables[envVarToInclude]
    return config


def substitute_variables(config: dict) -> tuple[dict, int] :
    """
    Performs variable substitutions in the configuration dictionary.

    Parameters
    ----------
    config
        The configuration dictionary.

    Returns
    -------
        The updated configuration dictionary after variable substitutions.
        The number of iterations performed for substitutions.
    """
    avail_keys = list(config.keys())
    iterationCount = 0
    while iterationCount < 10 :
        ## check if any entries in the config dictionary need populating
        foundToken = False
        for key, value in config.items() :
            if isinstance(value, str) :
                if (value.find('${') >= 0) :
                    foundToken = True
        ##
        if foundToken :
            for avail_key in avail_keys :
                key = '${%s}' % avail_key
                value = config[avail_key]
                for k in avail_keys :
                    if isinstance(config[k], str) :
                        if config[k].find(key) >= 0 :
                            config[k] = config[k].replace(key, value)
        else :
            break
        ##
        iterationCount += 1

    return config, iterationCount


def parse_boolean_keys(config: dict,
                       truevals: list[str] = ['true', '1', 't', 'y', 'yes'],
                       falsevals: list[str] = ['false', '0', 'f', 'n', 'no'],
                       bool_keys: list[str] = ["run_as_one_job", "submit_wrf_now", "submit_wps_component",
                                               "only_edit_namelists",
                                               "restart",
                                               'delete_metem_files', "use_high_res_sst_data",
                                               'regional_subset_of_grib_data']
                       ) :
    boolvals = truevals + falsevals

    for bool_key in bool_keys :
        assert (
                config[bool_key].lower() in boolvals
        ), f'Key {bool_key} not a recognised boolean value'
        config[bool_key] = (config[bool_key].lower() in truevals)

    return config


## function to parse times
def process_date_string(datestring) :
    datestring = datestring.strip().rstrip()

    ## get the timezone
    if len(datestring) <= 19 :
        tz = pytz.UTC
        date = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S')
    else :
        tzstr = datestring[20 :]
        tz = pytz.timezone(tzstr)
        date = datetime.datetime.strptime(datestring, '%Y-%m-%d %H:%M:%S %Z')

    date = tz.localize(date)

    return date


def load_wrf_config(filename: str) -> WRFConfig :
    input_str = read_config_file(filename)

    config = parse_config(input_str)

    config = add_environment_variables(config=config, environmental_variables=os.environ)

    config, iterationCount = substitute_variables(config)

    # Iteration count for filling variables
    assert iterationCount < 10, "Config key substitution exceeded iteration limit..."

    ## parse boolean keys
    # config = parse_boolean_keys(config)

    return WRFConfig(
        project_root=config['project_root'],
        setup_root=config['setup_root'],
        run_name=config['run_name'],
        target=config['target'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        restart=config['restart'],
        num_hours_per_run=config['num_hours_per_run'],
        num_hours_spin_up=config['num_hours_spin_up'],
        run_as_one_job=config['run_as_one_job'],
        submit_wrf_now=config['submit_wrf_now'],
        submit_wps_component=config['submit_wps_component'],
        environment_variables_for_substitutions=config[
            'environment_variables_for_substitutions'
        ],
        run_dir=config['run_dir'],
        run_script_template=config['run_script_template'],
        cleanup_script_template=config['cleanup_script_template'],
        main_script_template=config['main_script_template'],
        check_wrfout_in_background_script=config[
            'check_wrfout_in_background_script'
        ],
        only_edit_namelists=config['only_edit_namelists'],
        use_high_res_sst_data=config['use_high_res_sst_data'],
        wps_dir=config['wps_dir'],
        wrf_dir=config['wrf_dir'],
        nml_dir=config['nml_dir'],
        target_dir=config['target_dir'],
        scripts_to_copy_from_nml_dir=config['scripts_to_copy_from_nml_dir'],
        scripts_to_copy_from_target_dir=config[
            'scripts_to_copy_from_target_dir'
        ],
        metem_dir=config['metem_dir'],
        namelist_wps=config['namelist_wps'],
        namelist_wrf=config['namelist_wrf'],
        geog_data_path=config['geog_data_path'],
        geogrid_tbl=config['geogrid_tbl'],
        geogrid_exe=config['geogrid_exe'],
        ungrib_exe=config['ungrib_exe'],
        metgrid_tbl=config['metgrid_tbl'],
        metgrid_exe=config['metgrid_exe'],
        linkgrib_script=config['linkgrib_script'],
        wrf_exe=config['wrf_exe'],
        real_exe=config['real_exe'],
        delete_metem_files=config['delete_metem_files'],
        analysis_source=config['analysis_source'],
        orcid=config['orcid'],
        rda_ucar_edu_api_token=config['rda_ucar_edu_api_token'],
        regional_subset_of_grib_data=config['regional_subset_of_grib_data'],
        sst_monthly_dir=config['sst_monthly_dir'],
        sst_daily_dir=config['sst_daily_dir'],
        sst_monthly_pattern=config['sst_monthly_pattern'],
        sst_daily_pattern=config['sst_daily_pattern'],
        sst_vtable=config['sst_vtable'],
        analysis_pattern_upper=config['analysis_pattern_upper'],
        analysis_pattern_surface=config['analysis_pattern_surface'],
        analysis_vtable=config['analysis_vtable'],
        wrf_run_dir=config['wrf_run_dir'],
        wrf_run_tables_pattern=config['wrf_run_tables_pattern'],
        HOME=config['HOME'],
        USER=config['USER'],
        TMPDIR=config['TMPDIR'],
    )
