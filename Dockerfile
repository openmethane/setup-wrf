FROM ubuntu:20.04 as wgrib2

WORKDIR /src

ENV WGRIB2_VERSION="v2.0.8"

# Update the repo
RUN apt-get update && \
    apt-get install -y build-essential libaec-dev zlib1g-dev libcurl4-openssl-dev libboost-dev curl wget zip unzip bzip2 gfortran gcc g++


# Download the latest wgrib2 source code
RUN wget -c ftp://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/wgrib2.tgz.$WGRIB2_VERSION && \
    tar -xzvf wgrib2.tgz.$WGRIB2_VERSION && \
    cd grib2 && \
    CC=gcc FC=gfortran make

# Build the virtual environment in an isolated container
FROM python:3.11 as builder

RUN pip install poetry==1.8.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-ansi --no-root

# Container for running the project
# This isn't a hyper optimised container but it's a good starting point
FROM python:3.11

MAINTAINER Jared Lewis <jared.lewis@climate-resource.com>

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  OMPI_ALLOW_RUN_AS_ROOT=1 \
  OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# This is deliberately outside of the work directory
# so that the local directory can be mounted as a volume of testing
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Preference the libraries built in the WRF container for consistency
ENV LD_LIBRARY_PATH="/opt/wrf/libs/lib:${LD_LIBRARY_PATH}"

WORKDIR /opt/project

# Install additional apt dependencies
RUN apt-get update && \
    apt-get install -y libgfortran5 nco csh mpich bc libopenmpi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy across the virtual environment
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy in WRF and wgrib2 binaries
# https://github.com/climate-resource/wrf-container
COPY --from=ghcr.io/climate-resource/wrf:4.5.1 /opt/wrf /opt/wrf
COPY --from=ghcr.io/openmethane/cmaq:5.0.2 /opt/cmaq /opt/cmaq
COPY --from=wgrib2 /src/grib2/wgrib2/wgrib2 /usr/local/bin/wgrib2

# Copy in the rest of the project
# For testing it might be easier to mount $(PWD):/opt/project so that local changes are reflected in the container
COPY . /opt/project
COPY targets/docker/nccopy_compress_output.sh /opt/project/nccopy_compress_output.sh

# Install the local package in editable mode
RUN pip install -e .

CMD ["/bin/bash"]