import pytest
import os
from setup_runs.config_read_functions import read_config_file, parse_config, add_environment_variables, \
    substitute_variables


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
