# Secret management
FROM segment/chamber:2 AS chamber

# Build the reqired dependecies
FROM continuumio/miniconda3 as builder

# Install and package up the conda environment
# Creates a standalone environment in /opt/venv
COPY environment.yml /opt/environment.yml
RUN conda env create -f /opt/environment.yml
RUN conda install -c conda-forge conda-pack poetry=1.8.2
RUN conda-pack -n setup_wrf -o /tmp/env.tar && \
  mkdir /opt/venv && cd /opt/venv && \
  tar xf /tmp/env.tar && \
  rm /tmp/env.tar

# We've put venv in same path it'll be in final image,
# so now fix up paths:
RUN /opt/venv/bin/conda-unpack

# Install the python dependencies using poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_HOME='/opt/venv' \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# This is deliberately outside of the work directory
# so that the local directory can be mounted as a volume of testing
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Needed for wgrib2
RUN ln -s /opt/venv/lib/libnetcdf.so /opt/venv/lib/libnetcdf.so.13

WORKDIR /opt/venv

COPY pyproject.toml poetry.lock ./
RUN touch README.md

# This installs the python dependencies into /opt/venv
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    /opt/conda/bin/poetry install --no-ansi --no-root

# Container for running the project
# This isn't a hyper optimised container but it's a good starting point
FROM debian:bookworm

# These will be overwritten in GHA due to https://github.com/docker/metadata-action/issues/295
# These must be duplicated in .github/workflows/build_docker.yaml
LABEL org.opencontainers.image.title="Setup WRF"
LABEL org.opencontainers.image.description="Generate the scripts needed to run WRF according to configuration"
LABEL org.opencontainers.image.authors="Jared Lewis <jared.lewis@climate-resource.com>, Jeremy Silver <jeremy.silver@unimelb.edu.au>"
LABEL org.opencontainers.image.vendor="The Superpower Institute"

# SETUP_WRF_VERSION will be overridden in release builds with semver vX.Y.Z
ARG SETUP_WRF_VERSION=development
# Make the $SETUP_WRF_VERSION available as an env var inside the container
ENV SETUP_WRF_VERSION=$SETUP_WRF_VERSION

LABEL org.opencontainers.image.version="${SETUP_WRF_VERSION}"

# Configure Python
ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random

# This is deliberately outside of the work directory
# so that the local directory can be mounted as a volume of testing
ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Preference the environment libraries over the system libraries
ENV LD_LIBRARY_PATH="/opt/venv/lib:${LD_LIBRARY_PATH}"

WORKDIR /opt/project

# Install additional apt dependencies
RUN apt-get update && \
    apt-get install -y csh bc file make wget && \
    rm -rf /var/lib/apt/lists/*

# Secret management
COPY --from=chamber /chamber /bin/chamber

# Copy across the virtual environment
COPY --from=builder /opt/venv /opt/venv

# Copy in the WRF binaries
# https://github.com/climate-resource/docker-wrf
COPY --from=ghcr.io/climate-resource/wrf:4.5.1 /opt/wrf /opt/wrf

# Install the local package in editable mode
# Requires scaffolding the src directories
COPY pyproject.toml poetry.lock README.md ./
RUN mkdir -p src/setup_runs && touch src/setup_runs/__init__.py
RUN pip install -e .

# Copy in the rest of the project
# For testing it might be easier to mount $(PWD):/opt/project so that local changes are reflected in the container
COPY targets/docker/nccopy_compress_output.sh /opt/project/nccopy_compress_output.sh
COPY . /opt/project

CMD ["/bin/bash"]