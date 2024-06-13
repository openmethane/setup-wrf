"""
Watches the WRF output directory for new files and processes them in the background

Each output file is averaged into a single timestep and saved with a new filename.
This is required because WRF reports instantaneous values at each timestep.
Instead we want to average the values over a time period (in this case hourly).
If the file is successfully processed, the original file is removed.
"""

import datetime
from pathlib import Path

import netCDF4
import os
import time
import logging

from setup_runs.wrf.average_fields import average_fields


EXPECTED_TIMESTEPS = 12
"""
Number of timesteps in a completed file

Derived from the `frames_per_outfile` variable in the WRF namelist
"""

logger = logging.getLogger("check_wrfout_in_background")


def generate_out_filename(in_file: str):
    """
    Generate the filename of the averaged WRF output

    The WRF times in the filename are converted to ISO8601 format
    (with a trailing Z to indicate UTC time).
    These filenames play nicer with non-linux filesystems.
    """
    filename_chunks = in_file.split("_")
    time_str = "_".join(filename_chunks[2:])

    # Convert to iso8601 format
    date = datetime.datetime.strptime(time_str, "%Y-%m-%d_%H:%M:%S")
    filename_time = date.isoformat(timespec="minutes").replace(":", "")

    out_file = f"{filename_chunks[0].upper()}_{filename_chunks[1]}_{filename_time}Z.nc"
    return out_file, time_str


def process_file(in_file: Path):
    """
    Process a WRF output file into a single time step
    """
    nc = netCDF4.Dataset(in_file)
    ntimes = len(nc.dimensions["Time"])
    nc.close()
    if ntimes != EXPECTED_TIMESTEPS:
        logger.debug(
            "File %s has %d timesteps, expected %d", in_file, ntimes, EXPECTED_TIMESTEPS
        )
        return

    out_file, time_str = generate_out_filename(in_file.name)

    logger.info(f"Averaging {in_file} to {out_file}")
    try:
        average_fields(in_file, out_file, time_str)
    except Exception:
        logger.exception(f"Error processing {in_file}")
        return

    if not os.path.exists(out_file):
        logger.error("output file not created")
    else:
        logger.info("successfully processed. Removing old file")
        os.remove(in_file)


def main():
    while True:
        time.sleep(1)
        for inFile in Path(".").glob("wrfout_*"):
            mtimeAgo = time.time() - os.path.getmtime(inFile)
            logger.debug("found file %s mtimeago %d s", inFile, mtimeAgo)
            if mtimeAgo > 10.0:
                process_file(inFile)


if __name__ == "__main__":
    main()
