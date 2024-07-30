#!/usr/bin/env bash
# Runs the WRF model with the given configuration for a single day
#
# The output to archive will be stored in `data/wrf` directories by default.
#
# Future work
# - Cache the WRF geog data

set -Eeuo pipefail

DOMAIN=${DOMAIN:-aust-test}
RUN_DIR=${RUN_DIR:-/opt/project/data/wrf}
CONFIG_FILE=${CONFIG_FILE:-config/config.docker.json}
START_DATE=${START_DATE:-2022-07-22}

# Default end date is the next day
# Ignores the existing END_DATE variable if it is provided.
# setup-wrf uses a different date conventions compared to the rest of the OpenMethane project
END_DATE=$(date '+%Y-%m-%d' -d "$START_DATE+1 days")

# Steps of interest
python scripts/setup_for_wrf.py -c "${CONFIG_FILE}"
/opt/project/data/runs/${DOMAIN}/main.sh

echo "Finished"