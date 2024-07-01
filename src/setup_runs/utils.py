"""Utility functions used by a number of different functions"""

import subprocess
import os



def compressNCfile(filename, ppc=None):
    """Compress a netCDF3 file to netCDF4 using ncks

    Args:
        filename: Path to the netCDF3 file to commpress
        ppc: number of significant digits to retain (default is to retain all)

    Returns:
        Nothing
    """

    if os.path.exists(filename):
        print("Compress file {} with ncks".format(filename))
        command = "ncks -4 -L4 -O {} {}".format(filename, filename)
        print("\t" + command)
        commandList = command.split(" ")
        if ppc is None:
            ppcText = ""
        else:
            if not isinstance(ppc, int):
                raise RuntimeError("Argument ppc should be an integer...")
            elif ppc < 1 or ppc > 6:
                raise RuntimeError("Argument ppc should be between 1 and 6...")
            else:
                ppcText = "--ppc default={}".format(ppc)
                commandList = [commandList[0]] + ppcText.split(" ") + commandList[1:]
        ##
        ##
        p = subprocess.Popen(
            commandList, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate()
        if len(stderr) > 0 or len(stdout) > 0:
            print("stdout = " + stdout.decode())
            print("stderr = " + stderr.decode())
            raise RuntimeError("Error from ncks...")
    else:
        print("File {} not found...".format(filename))
