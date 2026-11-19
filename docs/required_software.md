# Required software

This repository pulls together a range of different software packages
to create a workflow for processing WRF data.
These packages are installed in different ways,
but are all brought together in a Docker container (see [../Dockerfile]())
The following table lists the software and versions that are required to run the workflow.

| Software | Version | Installation Method                              |
|----------|---------|--------------------------------------------------|
| Python   | 3.12    | uv, in the docker container                      |
| WRF      | 4.5.1   | docker base image (ghcr.io/openmethane/wrf:4.5.1) |
| MPICH    | 4.2.1   | docker base image                                |
| wgrib2   | 3.8.0   | built from source in the Dockerfile              |
| csh      | *       | Debian package                                   |
| NCO      | *       | Debian package                                   |
