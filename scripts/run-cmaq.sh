#!/usr/bin/env bash
# Runs the CMAQ setup scripts
#
# The output to archive will be stored in the `data/mcip` and `data/cmaq` directories.
#
# Future work
# - Specify start/end dates
# - Move CMAQ script to openmethane repo

set -Eeuo pipefail

CONFIG_FILE=${CONFIG_FILE:-config/cmaq/config.docker.json}

# Setup the prerequisites
# These may come from different places in future
if [[ ! -f data/inputs/cams_eac4_methane.nc ]]; then
  python scripts/download_cams_input.py \
      -s 2022-07-22 \
      -e 2022-07-22 \
      data/inputs/cams_eac4_methane.nc
fi

python scripts/setup_for_cmaq.py -c $CONFIG_FILE

echo "Finished"