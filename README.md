# WRF coordination scripts


## WRF runs

The `setup_for_wrf.py` script generates the required configuration and data to run WRF for a given domain and time.

`setup_for_wrf.py` uses a JSON configuration file to define
where the various input files are located, where the 
output files should be stored, and how the WRF model should be run. 
See [Input files](#input-files) for more information about how the configuration file is used.

`config.json` will be used as the default configuration file,
but this can be overriden using the `-c` command line argument.
An example config file `config.docker.json`that targets running WRF using docker.

The `setup_for_wrf.py` script does the following:
* Reads the configuration file
* Performs substitutions of the config file. For example, if used, the shell environment variable `${HOME}` will be replaced by its value when interpreting the script. The variable `wps_dir` is defined within the config file, and if the token `${wps_dir}` appears within the configuration entries, such tokens will be replaced by the value of this variable.
* Configure the main coordination script
* Loop over the required WRF jobs, performing the following:
  * Check if the WRF input files for this run are available (`wrfinput_d0?`). If not, perform the following:
    * Check that the geogrid files are available (copies should be found in the directory given by the config variable `nml_dir`). If not available, configure the WPS namelist and run `geogrid.exe` to produce them.
    * Check if the `met_em` files for this run are available. If not, perform the following:
      * Run `link_grib.csh`, configure the WPS namelist and run `ungrib.exe` for the high-resolution SST files (RTG) - this is optional
      * If using the NCEP FNL analysis (available from 2015-07-09), download and subset the grib files
      * Run `link_grib.csh`, configure the WPS namelist and run `ungrib.exe` for the analysis files (ERA Interim or FNL)
      * Run `metgrid.exe` to produce the `met_em` files, moves these to a directory (`METEM`)
    * Link to the `met_em` files (in the `METEM` directory), configure the WRF namelist, run `real.exe`
  * Configure the daily "run" and "cleanup" scripts


## Getting started

This repository supports two target environments to run.

### NCI 
**Updated to run on Gadi: these scripts no longer work on Raijin**

Procedure to run these scripts:
0. [Apply for membership](https://my.nci.org.au/) to the 'sx70' NCI group to use the `WPS_GEOG` dataset. If you also want to use the ERAI analyses, you will need to apply for access to the 'ua8' and 'ub4' NCI groups.
1. Edit the above scripts, particularly `config.json`, `namelist.wrf`, `namelist.wps`, `load_wrf_env.sh` (and possibly also `load_conda_env.sh`).
2. Either submit the setup via `qsub submit_setup.sh` *or* do the following:
..a. Log into one of the `copyq` nodes in interactive mode (via `qsub -I -q copyq -l wd,walltime=2:00:00,ncpus=1,mem=6GB -l storage=scratch/${PROJECT}+gdata/sx70+gdata/hh5`, for example).
..b. Run `./submit_setup.sh` on the command line. Before doing this, replace `${PROJECT}` in the `submit_setup.sh` script, with your `${PROJECT}` shell environment variable - this can be found in your `${HOME}/.config/gadi-login.conf` file.

To run the WRF model, either submit the main coordination script or the daily run-scripts with `qsub`.

#### A few caveats

This has been tested on *Gadi* using the [CLEX CMS WRF setup](https://github.com/coecms/WRF). Users of NCI wanting to run WRF are strongly encouraged to use this version, and to consult [the CMS page on WRF](http://climate-cms.wikis.unsw.edu.au/WRF). These scripts assume that WRF was compiled for MPI multiprocessing (i.e. 'distributed memory' parallelism). 


### docker

When not running on NCI, a docker container is recommended 
to reduce the complexity of setting up the required dependencies.
The Docker target can be run on any platform that supports docker,
including Windows, MacOS, and Linux.

This container can be built via:

```
docker build --platform=linux/amd64 . -t setup_wrf
```

Before running [static geographical data](https://www2.mmm.ucar.edu/wrf/users/download/get_sources_wps_geog.html) 
used by WPS must be downloaded and extracted locally.
This only needs to be performed once.

The highest resolution data are used in this case (~29 GB uncompressed).
These data were not included in the docker container given their size
and static nature. Instead, they are mounted as a local volume 
when running the docker container.

The required data can be downloaded and extracted to `data/geog` using the following command:

```
make data/geog
```

Once the static geography data has been extracted, 
the docker container containing the project dependencies can be run:

```
docker run --rm -it -v $(PWD):/project -v $(PWD)/data/geog/WPS_GEOG:/opt/wrf/geog setup_wrf
```

The static geographical data is mounted to `/opt/wrf/geog`.
The root project directory is also mounted to `/project` in the docker container. 
This allows for any changes made to this directory (or child directories) to be reflected
after the container is destroyed.

Inside the container, the wrf setup process can be run using the following command
(this might take some time):

```
python setup_for_wrf.py -c config.docker.json
```

This command will generate all the required configuration
and data required to run WRF in the `data/runs/` directory.
Depending on the time configuration,
multiple WRF jobs may be generated under the `data/runs/<run_name>` directory.


The `data/runs/<run_name>/main.sh` script generated in the previous step
can be used to run all the WRF jobs sequentially.
For each job, `main.sh` runs `data/runs/<run_name>/<YYYYMMDDHH>/run.sh`,
which runs WRF for the given time and domain.
Depending on the size of your domain and the number of processors available,
this may take some time.

`data/runs/<run_name>/<YYYYMMDDHH>/run.sh` can also be run directly 
to run WRF for a specific time period.

[TODO]: Add instructions for running CMAQ

## Input files

There are a number of files that are copied from various locations into the run directories. These are:

| File Name                    | Description                                                                    | Templated |
|------------------------------|--------------------------------------------------------------------------------|-----------|
| `cleanup_script_template.sh` | Template of per-run clean-up script                                            | Yes       |
| `main_script_template.sh`    | Template of the main coordination script                                       | Yes       |
| `run_script_template.sh`     | Template of the per-run run script                                             | Yes       |
| `namelist.wps`               | Template namelist for WPS                                                      | Yes       |
| `namelist.wrf`               | Template namelist for WRF                                                      | Yes       |
| `load_wrf_env.sh`            | Environment variables required to run WRF executables (same as to compile WRF) | No        |
| `nccopy_compress_output.sh`  | Script to compress any uncompressed netCDF3 files to deflated netCDF4          | No        |
| `add_remove_var.txt`         | List of variables to add/remove to the standard WRF output stream              | No        |


The non-templated files are copied from either the `nml_dir` or `target_dir` directories (as defined in `config.json`).
The location of the non-templated files is define using the `scripts_to_copy_from_nml_dir` and 
`scripts_to_copy_from_nml_dir` configuration values.

The templated files are configured based on the results of `config.json`
The tokens to replace are identified with the following format: `${keyword}`. 
Generally speaking, the values for substitution are defined within the python script (`setup_for_wrf.py`). 
To change the substitutions, edit the python script in the sections between the lines bounded by `## EDIT:` and `## end edit section`.

The `load_wrf_env.sh` script should contain the *same* environment modules that were used to compile WRF. 
It is assumed that you have compiled with MPI (i.e. 'distributed memory').


## Analysis inputs

This script will either use the ERA Interim reanalyses available on NCI or download NCEP FNL 0.25 analyses. This is set in `config.json`. If using the FNL analyses, you need to create an account on the [UCAR CISL](https://rda.ucar.edu) portal, and enter the credentials in `config.json` - this is not terribly secure, so make up a **fresh password** for this site. If switching between the FNL and ERA Interim reanalyses, you will need to change the Vtable file used (set in `config.json`), and also the number of vertical levels (set in `namelist.wrf` file). Also the merger of the RTG SSTs is only done for the ERA Interim analysis, and this step is optional (set in `config.json`).

## Notes on the structure of the output

All the main WRF output will be produced within subfolders of the directory given by variable `run_dir` in the config file. It will have the following substructure:
* `${run_dir}/metem`: contains any `met_em` files produced (once the `wrfinput_d0?` files have been created, these `met_em` files can be deleted).
* `${run_dir}/${YYYYMMDDHH}`: One folder per WRF run, where `${YYYYMMDDHH}` is the (UTC) date-stamp of the starting time of the corresponding WRF run (n.b. this run may actually start earlier if spinup is requested.
One exception to this is that the GEOGRID output files (`geo_em.d0?.nc`) are moved to the directory given by the variable `nml_dir` in the config file.

## General principles

The scripts have been developed with the following principles:
* Data should not be defined in multiple locations (or at least as few locations as possible)
* Symbolic links are used where possible in preference to new copies of data files, scripts and executables. When configuration is required, new copies are always generated.
* Inputs and outputs should be checked where possible and informative error messages should be given. Checks are fairly minimal (generally just that paths exist, not whether the contents are appropriate).
* The data footprint should be kept to a minimum.
* Progress is reported as the script progresses.

## General disclaimer

This software is provided "as is". I maintain it in the little spare time I have. I have limited time to debug things when they break, so please be prepared to solve problems yourself.
