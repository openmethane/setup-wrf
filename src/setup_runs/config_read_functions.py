import os
import sys
import json
import re
from typing import Tuple
import datetime
import pytz
from attrs import define

@define
class WRFConfig:
    project_root : str # overall base directory for project
    setup_root : str  # base dir for set up scripts
    run_name : str  # Project name
    target : str  # Target environment for running tasks
    start_date : str  # start first simulation, "%Y-%m-%d %H:%M:%S %Z" or just "%Y-%m-%d %H:%M:%S" for UTC
    end_date : str  # The end time of the last simulation (same format as above)
    # FIXME: this hasn't been fully implemented yet (only working for 'false')
    restart : str  # Is this a restart run? (bool -> true/false, yes/no)
    num_hours_per_run : int  # Number of hours of simulation of each run (excluding spin-up)
    num_hours_spin_up : int  # Number of hours of spin-up simulation of each run
    # TODO: add comments here? Or maybe better somewhere else?
    run_as_one_job : str
    submit_wrf_now : str
    submit_wps_component : str
    environment_variables_for_substitutions : str
    run_dir : str
    run_script_template : str
    cleanup_script_template : str
    main_script_template : str
    check_wrfout_in_background_script : str
    only_edit_namelists : str
    use_high_res_sst_data : str
    wps_dir : str
    wrf_dir : str
    nml_dir : str
    target_dir : str
    scripts_to_copy_from_nml_dir : str
    scripts_to_copy_from_target_dir : str
    metem_dir : str
    namelist_wps : str
    namelist_wrf : str
    geog_data_path : str
    geogrid_tbl : str
    geogrid_exe : str
    ungrib_exe : str
    metgrid_tbl : str
    metgrid_exe : str
    linkgrib_script : str
    wrf_exe : str
    real_exe : str
    delete_metem_files : str
    analysis_source : str
    orcid : str
    rda_ucar_edu_api_token : str
    regional_subset_of_grib_data : str
    sst_monthly_dir : str
    sst_daily_dir : str
    sst_monthly_pattern : str
    sst_daily_pattern : str
    sst_vtable : str
    analysis_pattern_upper : str
    analysis_pattern_surface : str
    analysis_vtable : str
    wrf_run_dir : str
    wrf_run_tables_pattern : str
    HOME : str
    USER : str
    TMPDIR : str

    def to_dict(self):
        d = {}
        for key in self.__dir__():
            d[d] = self.key
        return {key : self.key for key in self.__dir__() if not key.startswith('__') }


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
def process_date_string(datestring):
    datestring = datestring.strip().rstrip()
    ## get the timezone
    if len(datestring) <= 19:
        tz = pytz.UTC
    else:
        tzstr = datestring[20:]
        tz = pytz.timezone(tzstr)
    ##
    date = datetime.datetime.strptime(datestring,'%Y-%m-%d %H:%M:%S %Z')
    date = tz.localize(date)
    ##
    return date

def load_wrf_config(filename: str) -> WRFConfig:
    input_str = read_config_file(filename)

    config = parse_config(input_str)

    config = add_environment_variables(config=config, environmental_variables=os.environ)

    config, iterationCount = substitute_variables(config)

    # Iteration count for filling variables
    assert iterationCount < 10, "Config key substitution exceeded iteration limit..."

    ## parse boolean keys
    config = parse_boolean_keys(config)

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