import pytest
import os
from setup_runs.config_read_functions import (
    add_environment_variables,
    substitute_variables,
    boolean_converter,
    process_date_string,
)
from setup_runs.wrf.read_config_wrf import load_wrf_config, WRFConfig
from setup_runs.config_read_functions import load_json
from attrs import asdict


@pytest.fixture
def config_path_wrf_nci(root_dir):
    return os.path.join(root_dir, "config/config.nci.json")


@pytest.fixture
def config_path_wrf_docker(root_dir):
    return os.path.join(root_dir, "config/config.docker.json")


def test_add_environment_variable():
    config = {
        "some": "value",
        "more": "values",
        "environment_variables_for_substitutions": "HOME",
    }

    environment_variables = {
        "some": "value",
        "USER": "test_user",
        "HOME": "/Users/test_user",
    }

    expected = {
        "some": "value",
        "more": "values",
        "environment_variables_for_substitutions": "HOME",
        "HOME": "/Users/test_user",
    }

    assert (
        add_environment_variables(
            environment_variables=environment_variables, config=config
        )
        == expected
    )


def test_substitute_variables():
    config = {
        "level_zero": "level_zero_path",
        "level_one": "${level_zero}/test_path",
        "level_setup": "${level_one}/level_setup",
        "run_name": "test_run_123",
        "run_dir": "/scratch/q90/pjr563/openmethane-beta/wrf/${run_name}",
    }

    expected = {
        "level_zero": "level_zero_path",
        "level_one": "level_zero_path/test_path",
        "level_setup": "level_zero_path/test_path/level_setup",
        "run_name": "test_run_123",
        "run_dir": "/scratch/q90/pjr563/openmethane-beta/wrf/test_run_123",
    }

    out = substitute_variables(config)

    assert out == expected


def test_parse_boolean_keys():
    config = {
        "test_key_1": "t",
        "test_key_2": "1",
        "test_key_3": "true",
        "test_key_4": "y",
        "test_key_5": "yes",
        "test_key_6": "false",
        "test_key_7": "0",
        "test_key_8": "f",
        "test_key_9": "n",
        "test_key_10": "no",
        "test_key_11": "True",
        "test_key_12": "False",
    }

    expected = {
        "test_key_1": True,
        "test_key_2": True,
        "test_key_3": True,
        "test_key_4": True,
        "test_key_5": True,
        "test_key_6": False,
        "test_key_7": False,
        "test_key_8": False,
        "test_key_9": False,
        "test_key_10": False,
        "test_key_11": True,
        "test_key_12": False,
    }

    out = {k: boolean_converter(v) for k, v in config.items()}

    assert out == expected


@pytest.mark.parametrize(
    "datestring, expected",
    [
        pytest.param(
            "2024-01-01 00:00:00 UTC", "2024-01-01 00:00:00+00:00", id="UTC time zone"
        ),
        pytest.param(
            "2024-01-01 00:00:00", "2024-01-01 00:00:00+00:00", id="no time zone"
        ),
    ],
)
def test_process_date_string(datestring, expected):
    out = process_date_string(datestring)

    assert str(out) == expected


targets = pytest.mark.parametrize("target", ["nci", "docker"])


@targets
def test_config_values(target, config_path_wrf_nci, config_path_wrf_docker):
    if target == "nci":
        config = load_json(config_path_wrf_nci)
        # load config object (performs all of the above steps)
        wrf_config = load_wrf_config(config_path_wrf_nci)
    elif target == "docker":
        config = load_json(config_path_wrf_docker)
        wrf_config = load_wrf_config(config_path_wrf_docker)
    else:
        raise ValueError("Unknown target")

    for value_to_boolean in [
        "restart",
        "run_as_one_job",
        "submit_wrf_now",
        "submit_wps_component",
        "only_edit_namelists",
        "use_high_res_sst_data",
        "delete_metem_files",
        "regional_subset_of_grib_data",
    ]:
        config[value_to_boolean] = boolean_converter(config[value_to_boolean])

    # fill variables in the values with environment variables - e.g. '${HOME}' to '/Users/danielbusch'
    config = add_environment_variables(config=config, environment_variables=os.environ)

    # fill variables that depend on environment variables - e.g. "${HOME}/openmethane-beta" to "/Users/danielbusch/openmethane-beta"
    config = substitute_variables(config)

    # remove environment variables that were previously added
    for env_var in config["environment_variables_for_substitutions"].split(","):
        if env_var in config.keys():
            config.pop(env_var)

    # parse the dates
    config["end_date"] = process_date_string(config["end_date"])
    config["start_date"] = process_date_string(config["start_date"])

    assert config == asdict(wrf_config)


@pytest.fixture
def dynamic_wrf_nci_values():
    return [
        "run_script_template",
        "cleanup_script_template",
        "main_script_template",
        "check_wrfout_in_background_script",
        "nml_dir",
        "target_dir",
        "metem_dir",
        "namelist_wps",
        "namelist_wrf",
        "geogrid_tbl",
        "geogrid_exe",
        "ungrib_exe",
        "metgrid_tbl",
        "metgrid_exe",
        "linkgrib_script",
        "wrf_exe",
        "real_exe",
        "sst_vtable",
        "analysis_vtable",
        "wrf_run_dir",
        "setup_root",
        "wps_dir",
        "wrf_dir",
        "project_root",
    ]


@pytest.fixture
def dynamic_wrf_docker_values():
    return [
        "run_script_template",
        "cleanup_script_template",
        "main_script_template",
        "check_wrfout_in_background_script",
        "nml_dir",
        "target_dir",
        "metem_dir",
        "namelist_wps",
        "namelist_wrf",
        "geogrid_tbl",
        "geogrid_exe",
        "ungrib_exe",
        "metgrid_tbl",
        "metgrid_exe",
        "linkgrib_script",
        "wrf_exe",
        "real_exe",
        "sst_vtable",
        "analysis_vtable",
        "wrf_run_dir",
    ]


def test_nci_config_regression(
    config_path_wrf_nci, data_regression, dynamic_wrf_nci_values
):
    wrf_config = load_wrf_config(config_path_wrf_nci)
    data = asdict(wrf_config)

    for val in dynamic_wrf_nci_values:
        data.pop(val)

    data_regression.check(data)


def test_docker_config_regression(
    config_path_wrf_docker, data_regression, dynamic_wrf_docker_values
):
    wrf_config = load_wrf_config(config_path_wrf_docker)
    data = asdict(wrf_config)

    for val in dynamic_wrf_docker_values:
        data.pop(val)

    data_regression.check(data)


@pytest.fixture()
def wrf_config_dict(config_path_wrf_docker):
    return asdict(load_wrf_config(config_path_wrf_docker))


@pytest.mark.parametrize(
    "start_date, end_date, test_id",
    [
        ("2022-07-01 00:00:00 UTC", "2022-07-01 00:00:00 UTC", "test_same_day"),
        ("2022-07-01 00:00:00 UTC", "2022-07-02 00:00:00 UTC", "test_next_day"),
        ("2022-07-01 00:00:00 UTC", "2023-07-01 00:00:00 UTC", "test_next_year"),
    ],
    ids=lambda test_id: test_id,
)
def test_validator_end_date_after_start_date(
    start_date, end_date, test_id, wrf_config_dict
):
    wrf_config_dict["start_date"] = start_date
    wrf_config_dict["end_date"] = end_date

    wrf_config = WRFConfig(**wrf_config_dict)

    assert wrf_config.start_date
    assert wrf_config.end_date


# Error cases
@pytest.mark.parametrize(
    "start_date, end_date, test_id",
    [
        (
            "2022-07-02 00:00:00 UTC",
            "2022-07-01 00:00:00 UTC",
            "test_error_previous_day",
        ),
        (
            "2022-08-01 00:00:00 UTC",
            "2022-07-02 00:00:00 UTC",
            "test_error_previous_month",
        ),
        (
            "2024-07-01 00:00:00 UTC",
            "2023-07-01 00:00:00 UTC",
            "test_error_previous_year",
        ),
    ],
    ids=lambda test_id: test_id,
)
def test_validator_end_date_after_start_date_errors(
    start_date, end_date, test_id, wrf_config_dict
):
    wrf_config_dict["start_date"] = start_date
    wrf_config_dict["end_date"] = end_date

    with pytest.raises(ValueError, match="End date must be after start date."):
        WRFConfig(**wrf_config_dict)
