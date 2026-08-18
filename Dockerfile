# Secret management
FROM segment/chamber:2 AS chamber

# Build wgrib2
FROM debian:trixie-slim AS wgrib2-builder

ARG WGRIB2_VERSION="3.8.0"

ADD https://github.com/NOAA-EMC/wgrib2/archive/refs/tags/v${WGRIB2_VERSION}.tar.gz /tmp/wgrib2.tar.gz

RUN <<EOT
apt-get update -qy
apt-get install -qyy \
    -o APT::Install-Recommends=false \
    -o APT::Install-Suggests=false \
    ca-certificates \
    build-essential \
    cmake

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/apt-cache
EOT

# Unpack the source, build with the default (self-contained) CMake options and
# install into /opt/wgrib2, since wgrib2 isn't available as a debian package
RUN <<EOT
mkdir -p /opt/wgrib2-src
tar -xzf /tmp/wgrib2.tar.gz -C /opt/wgrib2-src --strip-components=1
rm /tmp/wgrib2.tar.gz

cmake \
    -S /opt/wgrib2-src \
    -B /opt/wgrib2-src/build \
    -DCMAKE_INSTALL_PREFIX=/opt/wgrib2 \
    -G "Unix Makefiles"
make -C /opt/wgrib2-src/build -j"$(nproc)"
make -C /opt/wgrib2-src/build install

rm -rf /opt/wgrib2-src
EOT

# Fetch python dependencies and build the application in the `/app` directory
FROM ghcr.io/astral-sh/uv:trixie-slim AS uv-builder

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

# Use a final image set up for WRF for our runtime environment
# https://github.com/openmethane/docker-wrf
FROM ghcr.io/openmethane/wrf:4.5.1

# Setup a non-root user
RUN groupadd --system --gid 1000 app \
 && useradd --system --gid 1000 --uid 1000 --create-home app

# Install the bare minimum software requirements on top of the WRF image
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
    nco \
    rsync \
    wget

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
EOT

# Use the non-root user to run our application
USER app

# Set the application folder as the working directory
WORKDIR /app

# Secret management
COPY --from=chamber /chamber /bin/chamber

# wgrib2
COPY --from=wgrib2-builder /opt/wgrib2 /opt/wgrib2
ENV PATH="/opt/wgrib2/bin:$PATH"

# Copy the Python version
COPY --from=builder --chown=python:python /python /python

ENV PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random

# Copy the application from the builder
COPY --from=uv-builder --chown=nonroot:nonroot /app /app

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

CMD ["bash"]