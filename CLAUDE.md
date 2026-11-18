# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

setup-wrf generates the namelists, shell scripts and input data needed to run WRF (via WPS: geogrid → ungrib → metgrid → real.exe) for a domain and date range, and runs it. It is the meteorology stage of Open Methane: its output becomes CMAQ's meteorological inputs through MCIP. Production runs the Docker image (built on `ghcr.io/openmethane/wrf:4.5.1`; CI pushes it to GHCR and ECR).

## Commands

Python 3.12, managed with `uv`. The package lives in `src/setup_runs` (imported as `setup_runs`); the scripts in `scripts/` import it.

```bash
make install                                   # uv sync
make test                                      # unit tests (tests/unit only)
uv run python -m pytest tests/unit/test_mpi_tasks.py::test_name -v   # single test
make test-regen                                # regenerate pytest-regressions fixtures
make changelog-draft                           # preview towncrier changelog
uv format -- <changed files>                   # ruff formatting
```

The code base isn't formatter-clean, so `make format` (whole repo) reformats files you didn't touch; format only the files you changed.

`tests/unit/test_read_config/` holds regression fixtures for `config.docker.json` and `config.nci.json`; run `make test-regen` when either config changes and check the fixture diff. `tests/integration` is a placeholder (`pass`); the real end-to-end check in CI is that `setup_for_wrf.py` and `main.sh` exit 0 inside the image.

### Running WRF locally

Needs Docker and the static geography data in `data/geog` (`make data/geog`, ~29 GB). `make run` uses `docker run -it`, which fails without a TTY, so from a non-interactive shell run its steps directly:

```bash
make build
docker run --rm -v $(PWD):/app -v /app/.venv setup-wrf python scripts/setup_for_wrf.py -c config/config.docker.json
docker run --rm -v $(PWD):/app -v /app/.venv setup-wrf /app/data/runs/aust-test/main.sh
```

The Docker configs set `geo_em_dir` to `${run_dir}`, so geogrid always runs (the `domains/*/geo_em.d01.nc` files are only used by `config.nci.json`). `scripts/download-geog.sh --low-res` is much smaller, but geogrid then only works if `geog_data_res` in the domain's `namelist.wps` is changed to `'usgs_10m+lowres'`, as CI does with `sed` in `.github/workflows/build_docker.yaml`.

## Architecture

- **`scripts/setup_for_wrf.py`** is the core: a single long click command (`-c <config.json>`; always pass it, the default path doesn't exist). It reads the config, reads the domain's template `namelist.wps`/`namelist.wrf` with `f90nml`, then for each job (`num_hours_per_run` chunks, plus `num_hours_spin_up`) creates `${run_dir}/<YYYYMMDDHH>/`, runs geogrid (unless `geo_em` files exist in `geo_em_dir`), fetches FNL analyses (`setup_runs/wrf/fetch_fnl.py`), runs ungrib/metgrid/real.exe, writes `namelist.input`, and renders `main.sh`, `run.sh`, `cleanup.sh` from templates. A `.env` file is loaded if present.
- **Config** (`config/*.json`) is parsed into the attrs `WRFConfig` class in `src/setup_runs/wrf/read_config_wrf.py`. Values support `${var}` substitution from other config keys and from env vars listed in `environment_variables_for_substitutions`. `run_name` also selects the domain (`nml_dir = domains/${run_name}`). `config.docker.json` is the fixed aust-test case; `config.docker.full.json` is the production config, driven by `START_DATE`, `END_DATE`, `CHK_PATH`, `DOMAIN_NAME`.
- **`scripts/run-wrf.sh`** is the production entrypoint for one day:
  - It always sets `END_DATE` to `START_DATE` + 1 day, ignoring any `END_DATE` passed in.
  - It works in `${CHK_PATH}/wrf/${DOMAIN_NAME}` and pulls the published `geo_em.d01.nc` (selected by `DOMAIN_VERSION`) from S3 if available.
  - It runs `setup_for_wrf.py` and `main.sh`. An EXIT trap rsyncs the results to `${STORE_PATH}/wrf/${DOMAIN_NAME}` and then `rm -rf`s the `CHK_PATH` run directory, even on failure.
  - It skips the run if complete `WRFOUT_*.nc` output already exists in `STORE_PATH`, unless `FORCE_WRF=true`. Leftover raw `wrfout_*` files count as incomplete.
- **`domains/<name>/`** holds per-domain `namelist.wps`, `namelist.wrf`, `add_remove_var.txt` (and sometimes `geo_em.d01.nc`). These describe the domain only (grid, physics). Settings for how WRF runs (e.g. `debug_level`, `use_netcdf_classic`, `history_begin_h`) are set in code in `setup_for_wrf.py` where `namelist.input` is generated, not in the domain files.
- **`targets/<docker|nci>/`** holds the shell templates (`main_script_template.sh`, `run_script_template.sh`, `cleanup_script_template.sh`) plus `load_wrf_env.sh` and `nccopy_compress_output.sh`; `config.target` selects the directory. Only `docker` is supported. The NCI target (`targets/nci`, `config.nci.json`, `submit_setup.sh`, `load_wrf_env.sh` at the root) is unsupported and expected to be deprecated, so don't spend effort keeping it in step with Docker changes. Templates contain `${keyword}` tokens, filled from the substitution dicts in the `## EDIT:` sections of `setup_for_wrf.py`.
- **Averaging:** the generated run script starts `scripts/check_wrfout_in_background.py --verify-steps` to average `wrfout` files (via `setup_runs/wrf/average_fields.py`) into `WRFOUT_*` files and remove the originals. It expects `EXPECTED_TIMESTEPS = 12` frames per file, matching `history_interval = 5` / `frames_per_outfile = 12` in the domain namelists. A domain with other values (e.g. `aust25km`, 60/1) is only averaged by `cleanup.sh` (`--no-verify-steps`).
- **MPI ranks:** `setup_runs/wrf/mpi_tasks.py` picks a safe MPI task count from the innermost domain's `geo_em` size and the physical CPU count. It is templated as `DEFAULT_NCPUS` in the Docker run script, and an `NCPUS` env var overrides it.

## Conventions

- Every PR needs a towncrier fragment in `changelog/` named `<PR number>.<type>.md` (types: breaking, deprecation, feature, improvement, fix, docs, trivial), written in past tense for users; use `trivial` for internal changes. Fill in `.github/pull_request_template.md`, starting with the **Review:** line; "Code review" in `docs/development.md` explains how to decide whether a PR needs review.
- Releases are cut by the "Create release" GitHub Action (see `docs/development.md`), which bumps the version, compiles `docs/changelog.md` and tags `vX.Y.Z`; don't bump versions by hand.

## Before opening a pull request

For any change that isn't mechanical (see "Code review" in
`docs/development.md`), review it from a fresh context before opening the
pull request, and again after reworking it substantially. Skip this for
formatter runs, dependency bumps and experiments not for merge, or if the
operator asks you to.

Launch the `reviewer` subagent (`.claude/agents/reviewer.md`). Give it:

- the goal of the change and the diff range (e.g. `main...HEAD`)
- the numbers of any issues the change addresses
- any constraints the operator set during the task, such as an approach to use
  or avoid, or something to leave unchanged

Don't give it your reasoning or your view of whether the change is correct,
because it will tend to confirm what it's told.

Independent reviews of the same change find different problems. When a change
both alters the WRF output or what production runs do, and touches error
handling, downloads, the Docker image, or several modules, offer the operator
a second review, run in parallel with the same brief. Each review costs tens
of thousands of tokens, so run the second only if the operator agrees. Merge
the two reports, counting a finding both raised once, before dealing with
them.

Deal with each item it reports:

- **Wrong, with a clear fix:** fix it, if the fix stays within the scope of the
  task and doesn't go against the operator's instructions or the project's
  guidance.
- **Needs the operator's decision:** ask the operator, with the options and
  your recommendation. This includes items with an obvious fix that would
  change the WRF output or methodology, widen the change beyond what was
  asked, or make the pull request need human review when it otherwise
  wouldn't.
- **Not a problem:** dismiss it, but list it in one line to the operator with
  your reason, because you're judging criticism of your own work.

This review is part of preparing the change. Don't mention it or its findings
in the pull request description or comments.
