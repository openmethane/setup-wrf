# Secret management
FROM segment/chamber:2 AS chamber

# First, build the application in the `/opt/project` directory
FROM ghcr.io/astral-sh/uv:trixie-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Configure the Python directory so it is consistent
ENV UV_PYTHON_INSTALL_DIR=/python

# Only use the managed Python version
ENV UV_PYTHON_PREFERENCE=only-managed

# Install Python before the project for caching
RUN uv python install 3.12

WORKDIR /app

# install dependencies from pyproject.toml without the app, to create a
# cacheable layer that changes less frequently than the app code
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# install the app + dependencies using the uv cache from the previous step
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# Then, use a final image without uv for our runtime environment
FROM debian:trixie-slim

# Setup a non-root user
RUN groupadd --system --gid 1000 app \
 && useradd --system --gid 1000 --uid 1000 --create-home app

# Install the bare minimum software requirements on top of trixie-slim
RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    ca-certificates \
    csh \
    bc \
    bzip2 \
    file \
    make \
    rsync \
    wget \
    libnetcdff7 \    # WRF dependency
    libpng16-16t64 \ # WRF dependency
    mpich            # WRF dependency

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

# Use the non-root user to run our application
USER app

# Set the application folder as the working directory
WORKDIR /app

# Secret management
COPY --from=chamber /chamber /bin/chamber

# Copy in the WRF binaries
# https://github.com/openmethane/docker-wrf
COPY --from=ghcr.io/openmethane/wrf:4.5.1 /opt/wrf /opt/wrf

# Copy the Python version
COPY --from=builder --chown=python:python /python /python

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
# Place the package root in the python import path so files in scripts/ can resolve
ENV PYTHONPATH="/app/src"

# Use `/app` as the working directory
WORKDIR /app

# These will be overwritten in GHA due to https://github.com/docker/metadata-action/issues/295
# These must be duplicated in .github/workflows/build_docker.yaml
LABEL org.opencontainers.image.title="Setup WRF"
LABEL org.opencontainers.image.description="Generate the scripts needed to run WRF according to configuration"
LABEL org.opencontainers.image.authors="Lindsay Gaines <lindsay.gaines@superpowerinstitute.com.au>, Jeremy Silver <jeremy.silver@unimelb.edu.au>"
LABEL org.opencontainers.image.vendor="The Superpower Institute"

# SETUP_WRF_VERSION will be overridden in release builds with semver vX.Y.Z
ARG SETUP_WRF_VERSION=development
# Make the $SETUP_WRF_VERSION available as an env var inside the container
ENV SETUP_WRF_VERSION=$SETUP_WRF_VERSION

LABEL org.opencontainers.image.version="${SETUP_WRF_VERSION}"

CMD ["/bin/bash"]