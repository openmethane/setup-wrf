"""Utility functions used by a number of different functions"""

import subprocess
import os


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

        p = subprocess.Popen(
            command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        if len(stderr) > 0 or len(stdout) > 0:
            print("stdout = " + stdout.decode())
            print("stderr = " + stderr.decode())
            raise RuntimeError("Error from ncks...")
    else:
        print("File {} not found...".format(filename))
