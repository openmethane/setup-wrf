#!/usr/bin/env bash
# Runs the WRF model with the given configuration for a single day
#
# The output to archive will be stored in `data/wrf` directories by default.
#
# Future work
# - Cache the WRF geog data

set -Eeuo pipefail

export DOMAIN_NAME=${DOMAIN_NAME:-aust-test}
export DOMAIN_VERSION=${DOMAIN_VERSION:-v1}
# Root directory for storing output (excluding the wrf/${DOMAIN_NAME} directory)
export STORE_PATH=${STORE_PATH:-/opt/project/data}
export START_DATE=${START_DATE:-2022-07-22}
# Note that currently the full docker config is the only one that supports `STORE_PATH`
CONFIG_FILE=${CONFIG_FILE:-config/config.docker.full.json}


# Default end date is the next day
# Ignores the existing END_DATE variable if it is provided.
# setup-wrf uses a different date conventions compared to the rest of the OpenMethane project
export END_DATE=$(date '+%Y-%m-%d' -d "$START_DATE+1 days")

RUN_DIR="${STORE_PATH}/wrf/${DOMAIN_NAME}"
OUTPUT_DIR="${RUN_DIR}/$(date -d ${START_DATE} +%Y%m%d00)"

# Check for the existence of WRFOUT output in the working folder.
# If they exist, setup-wrf has already been run and can exit early unless FORCE_WRF=true
FORCE_WRF=${FORCE_WRF:-false}
FOUND_WRF_OUTPUT=false
if [ -d "${OUTPUT_DIR}" ] && compgen -G "${OUTPUT_DIR}/WRFOUT_*.nc" > /dev/null; then
  echo "Found existing WRF output in ${OUTPUT_DIR}"

  if compgen -G "${OUTPUT_DIR}/wrfout_*" > /dev/null; then
    echo "WRF output is incomplete, reprocessing"
  else
    FOUND_WRF_OUTPUT=true
  fi
fi

if [ "$FOUND_WRF_OUTPUT" = true ] && [ ! "$FORCE_WRF" = true ]; then
  echo "Complete WRF output is present, skipping run-wrf"
  exit 0;
fi

# Try fetch the published domain
# If the domain isn't available it will be created by setup_for_wrf.py
wget -N -nv -P ${RUN_DIR} \
  "https://openmethane.s3.amazonaws.com/domains/${DOMAIN_NAME}/${DOMAIN_VERSION}/geo_em.d01.nc" \
  || echo "Domain file not found, will create it"

# Steps of interest
python scripts/setup_for_wrf.py -c "${CONFIG_FILE}"
${RUN_DIR}/main.sh
echo "Finished"
