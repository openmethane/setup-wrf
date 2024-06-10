import pytest
import os
from pathlib import Path
from setup_runs.config_read_functions import read_config_file, parse_config, add_environment_variables, \
    substitute_variables, boolean_converter, process_date_string, load_wrf_config

from attrs import asdict


@pytest.fixture
def root_dir() :
    return Path(__file__).parent.parent


@pytest.fixture
def config_path(root_dir) :
    return os.path.join(root_dir, "config.nci.json")


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
              "environment_variables_for_substitutions" : "HOME,USER,PROJECT,TMPDIR",
              }

    environmental_variables = {
        "some" : "value",
        'USER' : 'test_user',
        'HOME' : '/Users/test_user',
    }

    expected = {"some" : "value",
                "more" : "values",
                "environment_variables_for_substitutions" : "HOME,USER,PROJECT,TMPDIR",
                'USER' : 'test_user',
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

    # load config object
    wrf_config = load_wrf_config(config_path)

    assert config == asdict(wrf_config)
