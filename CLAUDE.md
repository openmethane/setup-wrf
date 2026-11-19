# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

setup-wrf generates the namelists, shell scripts and input data needed to run WRF (via WPS: geogrid → ungrib → metgrid → real.exe) for a domain and date range. It is part of Open Methane; the Docker image (`ghcr.io/openmethane/setup-wrf`, built on `ghcr.io/openmethane/wrf:4.5.1`) is what runs in production.

## Commands

Python 3.12, managed with `uv`. The package lives in `src/setup_runs` (imported as `setup_runs`); the scripts in `scripts/` import it.

```bash
make install                                   # uv sync
make test                                      # unit tests (tests/unit only)
uv run python -m pytest tests/unit/test_mpi_tasks.py::test_name -v   # single test
make test-regen                                # regenerate pytest-regressions data
make format                                    # uv format (ruff)
make changelog-draft                           # preview towncrier changelog
```

Running WRF end to end needs Docker and the static geography data (`make data/geog`, ~29 GB; CI uses `scripts/download-geog.sh --low-res`):

```bash
make build                                     # docker build --platform=linux/amd64 -t setup-wrf .
make run                                       # setup_for_wrf.py with config/config.docker.json, then data/runs/aust-test/main.sh
```

`tests/integration` only works after a WRF run has produced output in `data/` (CI runs it inside the image after `make run`-equivalent steps). Unit tests in CI also run inside the built image.

## Architecture

- **`scripts/setup_for_wrf.py`** is the core: a single long click command (`-c <config.json>`). It reads the config, reads the domain's template `namelist.wps`/`namelist.wrf` with `f90nml`, then for each job (`num_hours_per_run` chunks, plus `num_hours_spin_up`) creates `${run_dir}/<YYYYMMDDHH>/`, runs geogrid (unless `geo_em` files already exist), fetches FNL analyses (`setup_runs/wrf/fetch_fnl.py`), runs ungrib/metgrid/real.exe, writes `namelist.input`, and renders `main.sh`, `run.sh`, `cleanup.sh` from templates. A `.env` file is loaded if present.
- **Config** (`config/*.json`) is parsed into the attrs `WRFConfig` class in `src/setup_runs/wrf/read_config_wrf.py`. Values support `${var}` substitution from other config keys and from env vars listed in `environment_variables_for_substitutions`. `config.docker.json` is the fixed aust-test case; `config.docker.full.json` is the production config, driven by `START_DATE`, `END_DATE`, `CHK_PATH`, `DOMAIN_NAME`.
- **`scripts/run-wrf.sh`** is the production entrypoint for one day: works in `CHK_PATH`, pulls a published `geo_em.d01.nc` from S3 if available, runs `setup_for_wrf.py` + `main.sh`, and rsyncs results to `STORE_PATH` on exit. It skips work if complete `WRFOUT_*.nc` output already exists (unless `FORCE_WRF=true`).
- **`domains/<name>/`** holds per-domain `namelist.wps`, `namelist.wrf`, `add_remove_var.txt` (and sometimes `geo_em.d01.nc`). These describe the domain only (grid, physics). Settings for how WRF runs (e.g. `debug_level`, `use_netcdf_classic`, `history_begin_h`) are set in code in `setup_for_wrf.py` where `namelist.input` is generated, not in the domain files.
- **`targets/<docker|nci>/`** holds the shell templates (`main_script_template.sh`, `run_script_template.sh`, `cleanup_script_template.sh`, with `${keyword}` tokens substituted by `setup_for_wrf.py` in the `## EDIT:` sections) plus `load_wrf_env.sh` and `nccopy_compress_output.sh`. `config.target` selects the directory.
- `scripts/check_wrfout_in_background.py` is called by the generated run script to average `wrfout` files (via `setup_runs/wrf/average_fields.py`) into `WRFOUT_*` files and remove the originals.
- `setup_runs/wrf/mpi_tasks.py` picks a safe MPI task count from the domain size and physical CPU count.

## Conventions

- Every PR needs a towncrier fragment in `changelog/` named `<PR number>.<type>.md` (types: breaking, deprecation, feature, improvement, fix, docs, trivial), written in past tense for users. Fill in `.github/pull_request_template.md`.
- Releases are cut by the "Create release" GitHub Action (see `docs/development.md`), which bumps the version, compiles `docs/changelog.md` and tags `vX.Y.Z`; don't bump versions by hand.
