
# Development

## Docker images

A docker image will be built and made available through the GitHub Container
Registry for every push to `main` branch, as well as each PR.

See https://github.com/orgs/openmethane/packages for a list of available
packages.

### Resource metrics

The image entrypoint temporarily logs what each container costs, in the same
`[om-metrics]` format as the openmethane image: a `start` line with the CPUs
and memory the container could see, and a `finish` line with wall time, CPU
time, mean parallelism, throttling and memory high-water marks. See
`docs/reference/performance.md` in openmethane for how to read each field.

For `wrf-run`, the figures cover the whole container, including WPS and the
single-process `real.exe` as well as `wrf.exe`, so `mean_parallelism` will sit
below the MPI rank count. The `time` output that `run.sh` prints around
`mpirun` gives the `wrf.exe` step on its own.

Set `OM_METRICS=0` to turn the logging off. Interactive (`docker run -it`)
sessions are never measured.

## Preparing a release

When changes have been merged into `main` which should be used in prod or
released to the public, we follow a simple release process.

Visit the setup-wrf [Actions](https://github.com/openmethane/setup-wrf/actions)
page and select the
"[Create release](https://github.com/openmethane/setup-wrf/actions/workflows/release.yaml)"
action. Click the "Run workflow" button, leaving `main` as the selected branch.

Based on the content of the `changelog` folder in `main`, determine whether
this is a patch, minor or major release. Select that value in the workflow
dialogue, and click "Run workflow".

This workflow will:
- update the project version to the next semver version
- tag the repo with a `vX.Y.Z` tag
- update `docs/changelog.md` with the contents of the changelog items
- prepare a GitHub Release with the changelog content
- build and push a container image with the same version tag
