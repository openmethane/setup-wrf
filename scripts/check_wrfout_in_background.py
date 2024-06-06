"""
Watches the WRF output directory for new files and processes them in the background

Each output file is averaged into a single timestep and saved with a new filename.
This is required because WRF reports instantaneous values at each timestep.
Instead we want to average the values over a time period (in this case hourly).
If the file is successfully processed, the original file is removed.
"""

import datetime
from pathlib import Path

import click
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


def process_file(in_file: Path, expected_steps: int | None):
    """
    Process a WRF output file into a single time step

    Parameters
    ----------
    in_file
        File to process
    expected_steps
        The number of time steps expected in the input file
        Ignored if None.
    """
    if expected_steps is not None:
        with netCDF4.Dataset(in_file) as nc:
            ntimes = len(nc.dimensions["Time"])

        if ntimes != expected_steps:
            logger.debug(
                "File %s has %d timesteps, expected %d", in_file, ntimes, expected_steps
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


def process_files(file_pattern, expected_steps: int | None, timeout=10.0):
    """
    Check the WRF output directory for new files and process them

    Parameters
    ----------
    file_pattern
        Glob pattern used to find the files to process
    expected_steps
        The number of time steps expected in the input file
        Ignored if None.
    timeout
        Number of seconds since a file was last modified before it will be processed.
        Writing larger domains to disk may not be instantaneous.
    """
    for in_file in Path(".").glob(file_pattern):
        mtime_ago = time.time() - os.path.getmtime(in_file)
        logger.debug("found file %s mtimeago %d s", in_file, mtime_ago)
        if mtime_ago > timeout:
            process_file(in_file, expected_steps=expected_steps)


@click.command()
@click.option(
    "--timeout",
    help="Time to wait since last modified before processing",
    default=10.0,
    type=float,
)
@click.option(
    "-w",
    "--watch",
    help="Watch for any files matching the file pattern",
    is_flag=True,
)
@click.option(
    "--verify-steps/--no-verify-steps",
    help="Verify the that there are the expected number of steps in an output file."
         "This assumes that there are 12 x 5 minute steps.",
    default=False,
)
@click.argument("file_pattern", default="wrfout_*")
def main(file_pattern: str, watch: bool, timeout: float, verify_steps: bool):
    """
    Average raw WRF out files into hourly timesteps
    """
    if verify_steps:
        expected_steps = EXPECTED_TIMESTEPS
    else:
        logger.info("Not verifying the number of time steps in the wrf output")
        expected_steps = None

    if watch:
        # Keep checking until the process is killed
        while True:
            time.sleep(1)
            process_files(file_pattern, expected_steps=expected_steps, timeout=timeout)
    else:
        process_files(file_pattern, expected_steps=expected_steps, timeout=timeout)


if __name__ == "__main__":
    main()
