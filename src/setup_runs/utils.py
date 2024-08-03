"""Utility functions used by a number of different functions"""

import pathlib
import subprocess
import os
import re


def run_command(
    command_list: list[str], log_prefix: str | None = None, verbose: bool = False
) -> tuple[str, str]:
    p = subprocess.Popen(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    stdout = stdout.decode()
    stderr = stderr.decode()

    if log_prefix:
        with open(f"{log_prefix}.stdout", "w") as f:
            f.write(stdout)
        with open(f"{log_prefix}.stderr", "w") as f:
            f.write(stderr)

    if verbose or p.returncode != 0:
        print(f"Log from command: {command_list}")
        print(f"Exit Code: {p.returncode}")
        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")

    return stdout, stderr


def compress_nc_file(filename: str, ppc: int | None = None) -> None:
    """Compress a netCDF3 file to netCDF4 using ncks

    Args:
        filename: Path to the netCDF3 file to compress
        ppc: number of significant digits to retain (default is to retain all)

    Returns:
        Nothing
    """

    if os.path.exists(filename):
        print(f"Compress file {filename} with ncks")
        command = f"ncks -4 -L4 -O {filename} {filename}"
        print("\t" + command)
        command_list = command.split(" ")
        if ppc is not None:
            if not isinstance(ppc, int):
                raise RuntimeError("Argument ppc should be an integer...")
            elif ppc < 1 or ppc > 6:
                raise RuntimeError("Argument ppc should be between 1 and 6...")
            else:
                ppc_text = "--ppc default={}".format(ppc)
                command_list = (
                    [command_list[0]] + ppc_text.split(" ") + command_list[1:]
                )
        stdout, stderr = run_command(command_list)

        if len(stderr) > 0 or len(stdout) > 0:
            raise RuntimeError("Error from ncks...")
    else:
        print("File {} not found...".format(filename))


def purge(directory: str | pathlib.Path, pattern: str):
    for f in os.listdir(directory):
        if re.search(pattern, f) is not None:
            print("deleting:", pattern, "- file:", f)
            os.remove(os.path.join(directory, f))
