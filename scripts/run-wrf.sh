#!/usr/bin/env bash
# Runs the WRF model with the given configuration
#
# The output to archive will be stored in `data/runs` directories.
#
# Future work
# - Cache the WRF geog data
# - Specify start/end dates
# - Handle config files from the cmdline

set -Eeuo pipefail

CONFIG_FILE=${CONFIG_FILE:-config/config.docker.json}

# Steps of interest
python scripts/setup_for_wrf.py -c "${CONFIG_FILE}"
/opt/project/data/runs/aust-test/main.sh

echo "Finished"