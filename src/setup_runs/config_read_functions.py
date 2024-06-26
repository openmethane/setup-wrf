import json
import datetime
from typing import Mapping

import pytz


def boolean_converter(
    value: str,
    true_vals: list[str] = ("True", "true", "1", "t", "y", "yes"),
    false_vals: list[str] = ("False", "false", "0", "f", "n", "no"),
):
    """
    Convert a string value to a boolean based on predefined true and false values.

    Parameters
    ----------
    value
        The string value to be converted.
    true_vals
        List of strings considered as True values.
    false_vals
        List of strings considered as False values.

    Returns
    -------
        True if the value matches any of the truevals, False otherwise.

    """

    boolvals = true_vals + false_vals

    assert value.lower() in boolvals, f"Key {value} not a recognised boolean value"

    return value.lower() in true_vals


def add_environment_variables(
    config: dict[str, str | bool | int], environment_variables: Mapping[str, str]
) -> dict[str, str | bool | int]:
    """
    Add environment variables to the configuration that may be needed for substitutions.

    Parameters
    ----------
    config
        The configuration dictionary.
    environment_variables
        Process environment variables.

    Returns
    -------
        The updated configuration dictionary with added environment variables.

    """
    envVarsToInclude = config["environment_variables_for_substitutions"].split(",")

    for envVarToInclude in envVarsToInclude:
        config[envVarToInclude] = environment_variables[envVarToInclude]

    return config


def substitute_variables(
    config: dict[str, str | bool | int],
) -> dict[str, str | bool | int]:
    """
    Perform variable substitutions in the configuration dictionary.

    Parameters
    ----------
    config
        The configuration dictionary.

    Returns
    -------
        The updated configuration dictionary after variable substitutions.
    """
    avail_keys = list(config.keys())
    iterationCount = 0
    while iterationCount < 10:
        ## check if any entries in the config dictionary need populating
        foundToken = False
        for value in config.values():
            if isinstance(value, str) and value.find("${") >= 0:
                foundToken = True
        if not foundToken:
            break
        for avail_key in avail_keys:
            key = "${%s}" % avail_key
            value = config[avail_key]
            for k in avail_keys:
                if isinstance(config[k], str) and config[k].find(key) >= 0:
                    config[k] = config[k].replace(key, value)

        iterationCount += 1

    # Iteration count for filling variables
    assert iterationCount < 10, "Config key substitution exceeded iteration limit."

    return config


def process_date_string(date_str: str) -> datetime.datetime:
    """
    Process a date string to a datetime object with the appropriate timezone.

    Parameters
    ----------
    date_str
        The input date string to be processed.

    Returns
    -------
        The processed datetime object with the correct timezone
    """
    date_str = date_str.strip().rstrip()

    ## get the timezone
    if len(date_str) <= 19:
        tz = pytz.UTC
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    else:
        tzstr = date_str[20:]
        tz = pytz.timezone(tzstr)
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S %Z")

    return tz.localize(dt)


def load_json(filepath: str) -> dict[str, str | int | float]:
    """
    Loads and parses JSON data from a file.

    Parameters
    ----------
    filepath
        The path to the JSON file to load.

    Returns
    -------
        The parsed JSON data.
    """

    with open(filepath) as f:
        config = json.load(f)

    return config
