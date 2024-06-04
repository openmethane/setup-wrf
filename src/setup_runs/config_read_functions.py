import os
import sys
import json
import re
from typing import Tuple


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
