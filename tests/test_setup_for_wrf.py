import pytest
import os
from setup_runs.config_read_functions import read_config_file


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
    # Act
    content = read_config_file(temp_config_file)

    # Assert
    assert content == expected_content, "The content read from the file does not match the expected content."


def test_read_config_file_error_cases() :
    config_path = "path/to/non/existant/config.json"
    expected_exception = AssertionError
    expected_message = "No configuration file was found at path/to/non/existant/config.json"
    with pytest.raises(expected_exception) as exc_info :
        read_config_file(config_path)
    assert expected_message == str(exc_info.value)


