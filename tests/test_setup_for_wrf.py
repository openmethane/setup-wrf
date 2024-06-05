import pytest
import os
from setup_runs.config_read_functions import read_config_file, parse_config, add_environment_variables, \
    substitute_variables, parse_boolean_keys, process_date_string, load_wrf_config


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
def test_read_config_file_happy_path(temp_config_file, expected_content) :
    content = read_config_file(temp_config_file)

    assert content == expected_content, "The content read from the file does not match the expected content."


def test_read_config_file_error_cases() :
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
def test_parse_config_happy_path(input_str, expected) :
    result = parse_config(input_str)

    assert result == expected, "The parsed JSON does not match the expected output."


@pytest.mark.parametrize("input_str, expected",
                         [
                             pytest.param('{"missing": "trailing comma"', None, id="error_missing_trailing_comma"),
                             pytest.param('{"unquoted_key": value}', None, id="error_unquoted_key"),
                             pytest.param('not a json', None, id="error_not_json"),
                         ]
                         )
def test_parse_config_error_cases(input_str, expected, capsys) :
    with pytest.raises(SystemExit) :
        parse_config(input_str)

    captured = capsys.readouterr()
    assert "Problem parsing in configuration file" in captured.out


def test_add_environment_variable() :
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


def test_substitute_variables() :
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

    out, iterationCount = substitute_variables(config)

    assert iterationCount <= 10

    assert out == expected


def test_parse_boolean_keys() :
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
              "test_key" : "some string",
              }

    truevals = ['true', '1', 't', 'y', 'yes']

    falsevals = ['false', '0', 'f', 'n', 'no']

    bool_keys = ["test_key_1",
                 "test_key_2",
                 "test_key_3",
                 "test_key_4",
                 "test_key_5",
                 "test_key_6",
                 "test_key_7",
                 "test_key_8",
                 "test_key_9",
                 "test_key_10", ]

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
                "test_key" : "some string",
                }

    out = parse_boolean_keys(config=config,
                             truevals=truevals,
                             falsevals=falsevals,
                             bool_keys=bool_keys,
                             )
    assert out == expected


def test_requisite_keys_exist():

    # TODO: Fixture for config file
    configFile = '../config.nci.json'

    input_str = read_config_file(configFile)

    config = parse_config(input_str)

    requisite_keys = ["run_name", "start_date", "end_date"]
    for requisite_key in requisite_keys:
        assert (
            requisite_key in config.keys()
        ), f"Key {requisite_key} was not in the available configuration keys"


def test_process_date_string():
    pass

def test_dates_in_right_order():
    # TODO: Fixture for config file
    configFile = '../config.nci.json'

    input_str = read_config_file(configFile)

    config = parse_config(input_str)

    try :
        start_date = process_date_string(config['start_date'])
        end_date = process_date_string(config['end_date'])

        ## check that the dates are in the right order
        assert end_date > start_date, "End date should be after start date"
    except Exception as e :
        print("Problem parsing start/end times")
        raise e

def test_dates_in_right_order():
    # TODO: Fixture for config file
    configFile = '../config.nci.json'

    input_str = read_config_file(configFile)

    config = parse_config(input_str)
    # analysis source
    assert config['analysis_source'] in ['ERAI', 'FNL'], 'Key analysis_source must be one of ERAI or FNL'

def test_config_dict_regression():
    configFile = '../config.nci.json'

    input_str = read_config_file(configFile)

    config = parse_config(input_str)

    config = add_environment_variables(config=config, environmental_variables=os.environ)

    config, iterationCount = substitute_variables(config)

    ## parse boolean keys
    config = parse_boolean_keys(config)

    config_class = load_wrf_config(configFile)

    assert config == config_class.__getstate__()