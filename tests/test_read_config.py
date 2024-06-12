import pytest
import os
from pathlib import Path
from setup_runs.config_read_functions import read_config_file, parse_config, add_environment_variables, \
    substitute_variables, boolean_converter, process_date_string
from setup_runs.wrf.read_config_wrf import load_wrf_config
from setup_runs.cmaq.read_config_cmaq import load_json, create_cmaq_config_object
from attrs import asdict
import json


@pytest.fixture
def root_dir() :
    return Path(__file__).parent.parent


@pytest.fixture
def config_path(root_dir) :
    return os.path.join(root_dir, "config/wrf/config.nci.json")


@pytest.fixture
def config_cmaq_docker_path(root_dir) :
    return os.path.join(root_dir, "config/cmaq/config.docker.json")


@pytest.fixture
def config_cmaq_docker_dict(config_cmaq_docker_path) :
    return load_json(config_cmaq_docker_path)


@pytest.fixture
def input_str(config_path) :
    return read_config_file(config_path)


# Define a fixture for creating and deleting a temporary config file
@pytest.fixture
def temp_config_file(tmp_path, request) :
    content = request.param
    temp_file = tmp_path / "temp_config.json"
    temp_file.write_text(content)
    return str(temp_file)


@pytest.mark.parametrize(
    "temp_config_file, expected_content",
    [
        pytest.param("This is a test configuration.", "This is a test configuration.", id="simple_content"),
        pytest.param("", "", id="empty_file")
    ],
    indirect=["temp_config_file"]
)
def test_001_read_config_file_happy_path(temp_config_file, expected_content) :
    content = read_config_file(temp_config_file)

    assert content == expected_content, "The content read from the file does not match the expected content."


def test_002_read_config_file_error_cases() :
    config_path = "path/to/non/existant/config.json"
    expected_exception = AssertionError
    expected_message = "No configuration file was found at path/to/non/existant/config.json"
    with pytest.raises(expected_exception) as exc_info :
        read_config_file(config_path)
    assert expected_message == str(exc_info.value)


@pytest.mark.parametrize("input_str, expected",
                         [
                             pytest.param('{"key": "value"}', {"key" : "value"}, id="simple_json"),
                             pytest.param('{"number": 1234}', {"number" : 1234}, id="json_with_number"),
                             pytest.param('# This is a comment\n{"key": "value"}', {"key" : "value"},
                                          id="json_with_comment"),
                             pytest.param('{"nested": {"key": "value"}}', {"nested" : {"key" : "value"}},
                                          id="json_with_nested_object"),
                         ])
def test_003_parse_config_happy_path(input_str, expected) :
    result = parse_config(input_str)

    assert result == expected, "The parsed JSON does not match the expected output."


@pytest.mark.parametrize("input_str, expected",
                         [
                             pytest.param('{"missing": "trailing comma"', None, id="error_missing_trailing_comma"),
                             pytest.param('{"unquoted_key": value}', None, id="error_unquoted_key"),
                             pytest.param('not a json', None, id="error_not_json"),
                         ]
                         )
def test_004_parse_config_error_cases(input_str, expected, capsys) :
    with pytest.raises(SystemExit) :
        parse_config(input_str)

    captured = capsys.readouterr()
    assert "Problem parsing in configuration file" in captured.out


def test_005_add_environment_variable() :
    config = {"some" : "value",
              "more" : "values",
              "environment_variables_for_substitutions" : "HOME"  # ",USER,PROJECT,TMPDIR",
              }

    environmental_variables = {
        "some" : "value",
        'USER' : 'test_user',
        'HOME' : '/Users/test_user',
    }

    expected = {"some" : "value",
                "more" : "values",
                "environment_variables_for_substitutions" : "HOME",  # ,USER,PROJECT,TMPDIR",
                # 'USER' : 'test_user',
                'HOME' : '/Users/test_user',
                }

    assert add_environment_variables(environmental_variables=environmental_variables, config=config) == expected


def test_007_substitute_variables() :
    config = {
        'level_zero' : 'level_zero_path',
        'level_one' : '${level_zero}/test_path',
        'level_setup' : '${level_one}/level_setup',
        'run_name' : "test_run_123",
        'run_dir' : '/scratch/q90/pjr563/openmethane-beta/wrf/${run_name}',
    }

    expected = {
        'level_zero' : 'level_zero_path',
        'level_one' : 'level_zero_path/test_path',
        'level_setup' : 'level_zero_path/test_path/level_setup',
        'run_name' : "test_run_123",
        'run_dir' : '/scratch/q90/pjr563/openmethane-beta/wrf/test_run_123',
    }

    out = substitute_variables(config)

    assert out == expected


def test_008_parse_boolean_keys() :
    config = {"test_key_1" : "t",
              "test_key_2" : "1",
              "test_key_3" : "true",
              "test_key_4" : "y",
              "test_key_5" : "yes",
              "test_key_6" : "false",
              "test_key_7" : "0",
              "test_key_8" : "f",
              "test_key_9" : "n",
              "test_key_10" : "no",
              }

    expected = {"test_key_1" : True,
                "test_key_2" : True,
                "test_key_3" : True,
                "test_key_4" : True,
                "test_key_5" : True,
                "test_key_6" : False,
                "test_key_7" : False,
                "test_key_8" : False,
                "test_key_9" : False,
                "test_key_10" : False,
                }

    out = {k : boolean_converter(v) for k, v in config.items()}

    assert out == expected


def test_009_requisite_keys_exist(input_str) :
    config = parse_config(input_str)

    requisite_keys = ["run_name", "start_date", "end_date"]

    for requisite_key in requisite_keys :
        assert (
                requisite_key in config.keys()
        ), f"Key {requisite_key} was not in the available configuration keys"


@pytest.mark.parametrize("datestring, expected",
                         [
                             pytest.param('2024-01-01 00:00:00 UTC', '2024-01-01 00:00:00+00:00', id="UTC"),
                             pytest.param('2024-01-01 00:00:00 CET', '2024-01-01 00:00:00+01:00', id="CET"),
                             pytest.param('2024-01-01 00:00:00', '2024-01-01 00:00:00+00:00', id="no time zone"),
                         ]
                         )
def test_010_process_date_string(datestring, expected) :
    out = process_date_string(datestring)

    assert str(out) == expected


def test_011_dates_in_right_order(input_str) :
    config = parse_config(input_str)

    try :
        start_date = process_date_string(config['start_date'])
        end_date = process_date_string(config['end_date'])

        ## check that the dates are in the right order
        assert end_date > start_date, "End date should be after start date"
    except Exception as e :
        print("Problem parsing start/end times")
        raise e


def test_012_config_object(input_str, config_path) :
    config = parse_config(input_str)

    for value_to_boolean in ["restart",
                             "run_as_one_job",
                             "submit_wrf_now",
                             "submit_wps_component",
                             "only_edit_namelists",
                             "use_high_res_sst_data",
                             "delete_metem_files",
                             "regional_subset_of_grib_data", ] :
        config[value_to_boolean] = boolean_converter(config[value_to_boolean])

    # fill variables in the values with environment variables - e.g. '${HOME}' to '/Users/danielbusch'
    config = add_environment_variables(config=config, environmental_variables=os.environ)

    # fill variables that depend on environment variables - e.g. "${HOME}/openmethane-beta" to "/Users/danielbusch/openmethane-beta"
    config = substitute_variables(config)

    # remove environment variables that were previously added
    for env_var in config["environment_variables_for_substitutions"].split(',') :
        if env_var in config.keys() :
            config.pop(env_var)

    # load config object (performs all of the above steps)
    wrf_config = load_wrf_config(config_path)

    assert config == asdict(wrf_config)


@pytest.fixture
def valid_cmaq_config() :
    return {'CMAQdir' : '/opt/cmaq/CMAQv5.0.2_notpollen/',
            'MCIPdir' : '/opt/cmaq/CMAQv5.0.2_notpollen/scripts/mcip/src',
            'templateDir' : '/opt/project/templateRunScripts', 'metDir' : '/opt/project/data/mcip/',
            'ctmDir' : '/opt/project/data/cmaq/', 'wrfDir' : '/opt/project/data/runs/aust-test',
            'geoDir' : '/opt/project/templates/aust-test/',
            'inputCAMSFile' : '/opt/project/data/inputs/cams_eac4_methane.nc',
            'sufadj' : 'output_newMet', 'domains' : ['d01'], 'run' : 'openmethane',
            'startDate' : '2022-07-01 00:00:00 UTC',
            'endDate' : '2022-07-01 00:00:00 UTC', 'nhoursPerRun' : 24, 'printFreqHours' : 1,
            'mech' : 'CH4only',
            'mechCMAQ' : 'CH4only', 'prepareICandBC' : 'True', 'prepareRunScripts' : 'True',
            'add_qsnow' : 'False',
            'forceUpdateMcip' : 'False', 'forceUpdateICandBC' : 'True', 'forceUpdateRunScripts' : 'True',
            'scenarioTag' : ['220701_aust-test'], 'mapProjName' : ['LamCon_34S_150E'],
            'gridName' : ['openmethane'],
            'doCompress' : 'True', 'compressScript' : '/opt/project/nccopy_compress_output.sh',
            'scripts' : {'mcipRun' : {'path' : '/opt/project/templateRunScripts/run.mcip'},
                         'bconRun' : {'path' : '/opt/project/templateRunScripts/run.bcon'},
                         'iconRun' : {'path' : '/opt/project/templateRunScripts/run.icon'},
                         'cctmRun' : {'path' : '/opt/project/templateRunScripts/run.cctm'},
                         'cmaqRun' : {'path' : '/opt/project/templateRunScripts/runCMAQ.sh'}},
            'cctmExec' : 'ADJOINT_FWD',
            'CAMSToCmaqBiasCorrect' : 0.06700000000000017}


@pytest.mark.parametrize("value, expected_exception, test_id", [
    # Valid config tests
    ("cb05e51_ae6_aq", None, "happy_cb05e51"),
    ("cb05mp51_ae6_aq", None, "happy_cb05mp51"),
    ("saprc07tic_ae6i_aqkmti", None, "happy_saprc07tic"),
    ("CH4only", None, "happy_CH4only"),
    # Error cases
    ("cb06e51_ae6_aqooo", ValueError, "error_typo_in_mechanism"),
    ("", ValueError, "error_empty_string"),
    ("unknown_mechanism", ValueError, "error_unknown_mechanism"),
    (123, ValueError, "error_non_string_value"),
])
def test_013_check_mechCMAQ_validator(value, expected_exception, test_id, valid_cmaq_config) :
    cmaq_config = valid_cmaq_config.copy()

    cmaq_config['mechCMAQ'] = value

    if expected_exception :
        with pytest.raises(expected_exception) as exc_info :
            create_cmaq_config_object(cmaq_config)
        assert "Configuration value for mechCMAQ must be one of" in str(exc_info.value), f"Test Failed: {test_id}"
    else :
        try :
            create_cmaq_config_object(cmaq_config)
        except ValueError as e :
            pytest.fail(f"Unexpected ValueError raised for {test_id}: {e}")


@pytest.mark.parametrize("attribute, value, error_string",
                         [
                             ("scenarioTag", ["more_than_16_characters_long"],
                              "16-character maximum length for configuration value "),
                             ("scenarioTag", "not_a_list", "must be a list"),
                             ("gridName", ["more_than_16_characters_long"],
                              "16-character maximum length for configuration value "),
                             ("gridName", "not_a_list", "must be a list"),
                         ])
def test_014_check_max_16_characters_validators(attribute, value, error_string, valid_cmaq_config) :
    cmaq_config = valid_cmaq_config.copy()

    cmaq_config[attribute] = value

    with pytest.raises(ValueError) as exc_info :
        create_cmaq_config_object(cmaq_config)
    assert error_string in str(exc_info.value)


# Parametrized test for happy path scenarios
@pytest.mark.parametrize("input_value, test_id", [
    ({"mcipRun" : {"path" : "some/path"}, "bconRun" : {"path" : "some/path"}, "iconRun" : {"path" : "some/path"},
      "cctmRun" : {"path" : "some/path"}, "cmaqRun" : {"path" : "some/path"}}, "all_keys_present"),
    ({"mcipRun" : {"path" : "unique/path1"}, "bconRun" : {"path" : "unique/path2"},
      "iconRun" : {"path" : "unique/path3"}, "cctmRun" : {"path" : "unique/path4"},
      "cmaqRun" : {"path" : "unique/path5"}}, "unique_paths_for_all"),
], ids=["all_keys_present", "unique_paths_for_all"])
def test_015_check_happy_path(input_value, test_id, valid_cmaq_config) :
    cmaq_config = valid_cmaq_config.copy()

    cmaq_config["scripts"] = input_value

    try :
        create_cmaq_config_object(cmaq_config)
    except ValueError :
        pytest.fail("Unexpected ValueError raised.")


@pytest.mark.parametrize("input_value, expected_exception_message, test_id", [
    ({"mcipRun" : {}, "bconRun" : {}, "iconRun" : {}, "cctmRun" : {}, "cmaqRun" : {}},
     "mcipRun in configuration value scripts must have the key 'path'", "missing_path_in_all"),
    ({"mcipRun" : {"path" : "some/path"}, "bconRun" : {"path" : "some/path"}, "iconRun" : {},
      "cctmRun" : {"path" : "some/path"}, "cmaqRun" : {"path" : "some/path"}},
     "iconRun in configuration value scripts must have the key 'path'", "missing_path_in_one"),
    ({"mcipRun" : {"path" : "some/path"}},
     "scripts must have the keys ['mcipRun', 'bconRun', 'iconRun', 'cctmRun', 'cmaqRun']", "missing_keys"),
    ({}, "scripts must have the keys ['mcipRun', 'bconRun', 'iconRun', 'cctmRun', 'cmaqRun']", "empty_dict"),
], ids=["missing_path_in_all", "missing_path_in_one", "missing_keys", "empty_dict"])
def test_016_check_error_cases(input_value, expected_exception_message, test_id, valid_cmaq_config) :
    cmaq_config = valid_cmaq_config.copy()

    cmaq_config["scripts"] = input_value

    with pytest.raises(ValueError) as exc_info :
        create_cmaq_config_object(cmaq_config)
    assert expected_exception_message in str(exc_info.value), f"Test ID: {test_id}"


@pytest.mark.parametrize(
    "test_input, expected",
    [
        pytest.param("test_json_1.json", {'key': 'value'}, id="simple_content"),
        pytest.param("test_json_2.json", {
            'more_complex': 'content',
            'int': 1,
            'nested_dict' : {'nested': 'dict', 'bool' : "True"}
        }, id="more_complex_content"),])
def test_017_read_cmaq_json_config_file_happy_path(test_input, expected, tmp_path) :
    # Create a temporary directory and write the test data to a file
    test_file = tmp_path / test_input
    with open(test_file, "w") as f:
        json.dump(expected, f)
    expected_path = str(test_file)

    result = load_json(expected_path)

    assert result == expected, f"Failed to load or match JSON content for {test_input}"