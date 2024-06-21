#!/usr/bin/env bash
# Runs the WRF model with the given configuration
#
# The output to archive will be stored in `data/runs`, `data/mcip` and `data/cmaq` directories.
#
# Future work
# - Cache the WRF geog data
# - Specify start/end dates
# - Move CMAQ script to openmethane repo

set -Eeuo pipefail

# Setup the prerequisites
# These may come from different places in future
./scripts/download-geog.sh --low-res
if [[ ! -f data/inputs/cams_eac4_methane.nc ]]; then
  python scripts/download_cams_input.py \
      -s 2022-07-22 \
      -e 2022-07-22 \
      data/inputs/cams_eac4_methane.nc
fi

# Steps of interest
python scripts/setup_for_wrf.py -c config/wrf/config.docker.json
/opt/project/data/runs/aust-test/main.sh
python scripts/setup_for_cmaq.py