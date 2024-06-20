from attrs import define, field
import os
from setup_runs.config_read_functions import (
    boolean_converter,
    read_config_file,
    parse_config,
    add_environment_variables,
    substitute_variables,
    process_date_string
)


@define
class WRFConfig:
    project_root: str
    """overall base directory for project"""
    setup_root: str
    """" base dir for set up scripts """
    run_name: str
    """Project name """
    target: str
    """Target environment for running tasks"""
    start_date: str = field(converter=process_date_string)
    """start first simulation, "%Y-%m-%d %H:%M:%S %Z" or just "%Y-%m-%d %H:%M:%S" for UTC"""
    end_date: str = field(converter=process_date_string)
    """The end time of the last simulation (same format as above)"""

    @end_date.validator
    def check_endDate(self, attribute, value) :
        if value < self.start_date :
            raise ValueError("End date must be after start date.")

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
    """Submit the WRF runs at the end of the script? (bool -> true/false, yes/no)"""
    # FIXME: this hasn't been fully implemented yet (only working for 'false')
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
    analysis_source: str = field()
    """analysis source - can be ERAI or FNL"""

    @analysis_source.validator
    def check(self, attribute, value):
        if value not in ["FNL", "ERAI"]:
            raise ValueError("analysis_source must be one of ERAI or FNL")

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
    """pattern for matching the full-atmosphere analysis files (date-time substitutions 
    recognised as well as shell wildcards)"""
    analysis_pattern_surface: str
    """pattern for matching the surface-level analysis files (date-time substitutions 
    recognised as well as shell wildcards)"""
    analysis_vtable: str
    """VTable file for the SST analysis files"""
    wrf_run_dir: str
    """directory containing WRF input tables and data-files"""
    wrf_run_tables_pattern: str
    """pattern to match to get the WRF input tables and data-files 
    (within the folder ${wrf_run_dir}"""


def load_wrf_config(filename: str) -> WRFConfig:
    """
    Load and processes a WRF configuration file and create a WRFConfig object.

    Parameters
    ----------
    filename
        The path to the WRF configuration file.

    Returns
    -------
    WRFConfig
        An instance of the WRFConfig class initialized with the
        processed configuration data.
    """

    input_str = read_config_file(filename)

    config = parse_config(input_str)

    # fill variables in the values with environment variables
    # - e.g. '${HOME}' to '/Users/danielbusch'
    config = add_environment_variables(config=config, environment_variables=os.environ)

    # fill variables that depend on environment variables
    # - e.g. "${HOME}/openmethane-beta" to "/Users/danielbusch/openmethane-beta"
    config = substitute_variables(config)

    # remove environment variables that were previously added
    for env_var in config["environment_variables_for_substitutions"].split(","):
        config.pop(env_var)

    return WRFConfig(**config)
