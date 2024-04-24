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

WORKDIR /project

# Install libgfortran and nco dependencies
RUN apt-get update && \
    apt-get install -y libgfortran5 nco && \
    rm -rf /var/lib/apt/lists/*

# Setup poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Copy in WRF binaries
# https://github.com/climate-resource/wrf-container
COPY --from=ghcr.io/climate-resource/wrf:4.5.1 /opt/wrf /opt/wrf

# Setup project dependencies
COPY pyproject.toml /project/
RUN poetry install  --no-interaction --no-ansi

# Copy in the rest of the project
# For testing it might be easier to mount $(PWD):/project so that local changes are reflected in the container
COPY . /project

ENTRYPOINT ["/bin/bash"]