# Required software

This repository pulls together a range of different software packages
to create a workflow for processing WRF data.
These packages are installed in different ways,
but are all brought together in a Docker container (see [../Dockerfile]())
The following table lists the software and versions that are required to run the workflow.

| Software | Version | Installation Method                                   |
|----------|---------|-------------------------------------------------------|
| Python   | 3.11    | docker container                                      |
| WRF      | 4.5.1   | docker container (ghcr.io/climate-resource/wrf:4.5.1) |
| wgrib2   | 2.0.8   | conda                                                 |
| csh      | *       | conda                                                 |
| mpich    | 4.2.1   | conda                                                 |
| NCO      | *       | conda                                                 |