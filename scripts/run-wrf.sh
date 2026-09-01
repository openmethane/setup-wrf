#!/usr/bin/env bash
# Runs the WRF model with the given configuration for a single day
#
# The output to archive will be stored in `data/wrf` directories by default.
#
# Future work
# - Cache the WRF geog data

set -Eeuo pipefail

trap sync_output EXIT

export DOMAIN_NAME=${DOMAIN_NAME:-au-test}
export DOMAIN_VERSION=${DOMAIN_VERSION:-v1}
export START_DATE=${START_DATE:-2022-07-22}

# Root directory for storing output, will have "wrf/${DOMAIN_NAME}" appended
export STORE_PATH=${STORE_PATH:-/app/data}
# Checkpoint dir, used for high I/O workloads
export CHK_PATH=${CHK_PATH:-/mnt/scratch}
# Note that currently the full docker config is the only one that supports `STORE_PATH`
CONFIG_FILE=${CONFIG_FILE:-config/config.docker.full.json}


# Default end date is the next day
# Ignores the existing END_DATE variable if it is provided.
# setup-wrf uses a different date conventions compared to the rest of the OpenMethane project
export END_DATE=$(date '+%Y-%m-%d' -d "$START_DATE+1 days")

# Set up output and run paths. setup_for_wrf.py will use RUN_DIR as the working
# folder, which will see high I/O during processing. OUTPUT_DIR is the folder
# where final output should be stored.
OUTPUT_DIR="${STORE_PATH}/wrf/${DOMAIN_NAME}"
RUN_DIR="${CHK_PATH}/wrf/${DOMAIN_NAME}"
mkdir -p "${RUN_DIR}"

# In the case of failure, ensure partial output is moved to OUTPUT_DIR
sync_output() {
  # copy any results from RUN_DIR to OUTPUT_DIR
  echo "Copying completed output from ${RUN_DIR} to ${OUTPUT_DIR}"
  mkdir -p "${OUTPUT_DIR}"
  rsync -auv "${RUN_DIR}/" "${OUTPUT_DIR}/"

  echo "Removing temporary RUN_DIR: ${RUN_DIR}"
  rm -rf "${RUN_DIR}"
}

# Check for the existence of WRFOUT output in the working folder.
# If they exist, setup-wrf has already been run and can exit early unless FORCE_WRF=true
FORCE_WRF=${FORCE_WRF:-false}
FOUND_WRF_OUTPUT=false
OUTPUT_DIR_WITH_DATE="${OUTPUT_DIR}/$(date -d ${START_DATE} +%Y%m%d00)"
if [ -d "${OUTPUT_DIR_WITH_DATE}" ] && compgen -G "${OUTPUT_DIR_WITH_DATE}/WRFOUT_*.nc" > /dev/null; then
  echo "Found existing WRF output in ${OUTPUT_DIR_WITH_DATE}"

  if compgen -G "${OUTPUT_DIR_WITH_DATE}/wrfout_*" > /dev/null; then
    echo "WRF output is incomplete, reprocessing"
  else
    FOUND_WRF_OUTPUT=true
  fi
fi

if [ "$FOUND_WRF_OUTPUT" = true ] && [ ! "$FORCE_WRF" = true ]; then
  echo "Complete WRF output is present, skipping run-wrf"
  exit 0;
fi

# copy any pre-existing data from OUTPUT_DIR to RUN_DIR
if [ -d "${OUTPUT_DIR_WITH_DATE}" ]; then
  echo "Copying existing output from ${OUTPUT_DIR} to ${RUN_DIR}"
  rsync -auv "${OUTPUT_DIR}/" "${RUN_DIR}/"
fi

# Try fetch the published domain
# If the domain isn't available it will be created by setup_for_wrf.py
wget -N -nv -P ${RUN_DIR} \
  "https://openmethane.s3.amazonaws.com/domains/${DOMAIN_NAME}/${DOMAIN_VERSION}/geo_em.d01.nc" \
  || echo "Domain file not found, will create it"

# Steps of interest
python scripts/setup_for_wrf.py -c "${CONFIG_FILE}"
${RUN_DIR}/main.sh

echo "Finished successfully"
