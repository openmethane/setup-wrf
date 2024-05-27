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


# Container for running WRF
FROM python:3.11

MAINTAINER Jared Lewis <jared.lewis@climate-resource.com>

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PIP_NO_CACHE_DIR=off \
  PIP_DISABLE_PIP_VERSION_CHECK=on \
  PIP_DEFAULT_TIMEOUT=100 \
  POETRY_NO_INTERACTION=1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local' \
  POETRY_VERSION=1.8.2

# Preference the libraries built in the WRF container
ENV LD_LIBRARY_PATH="/opt/wrf/libs/lib:${LD_LIBRARY_PATH}"

WORKDIR /opt/project

# Install additional apt dependencies
RUN apt-get update && \
    apt-get install -y libgfortran5 nco csh mpich && \
    rm -rf /var/lib/apt/lists/*

# Setup poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Setup project dependencies
COPY pyproject.toml /opt/project/
RUN poetry install  --no-interaction --no-ansi

# Copy in WRF and wgrib2 binaries
# https://github.com/climate-resource/wrf-container
COPY --from=ghcr.io/climate-resource/wrf:4.5.1 /opt/wrf /opt/wrf
COPY --from=ghcr.io/openmethane/cmaq:5.0.2 /opt/cmaq /opt/cmaq
COPY --from=wgrib2 /src/grib2/wgrib2/wgrib2 /usr/local/bin/wgrib2

# Copy in the rest of the project
# For testing it might be easier to mount $(PWD):/opt/project so that local changes are reflected in the container
COPY . /opt/project

CMD ["/bin/bash"]