# Changelog

Versions follow [Semantic Versioning](https://semver.org/) (`<major>.<minor>.<patch>`).

Backward incompatible (breaking) changes will only be introduced in major versions
with advance notice in the **Deprecations** section of releases.


<!--
You should *NOT* be adding new changelog entries to this file, this
file is managed by towncrier. See changelog/README.md.

You *may* edit previous changelogs to fix problems like typo corrections or such.
To add a new changelog entry, please see
https://pip.pypa.io/en/latest/development/contributing/#news-entries,
noting that we use the `changelog` directory instead of news, md instead
of rst and use slightly different categories.
-->

<!-- towncrier release notes start -->

## setup-wrf v0.7.3 (2026-02-23)

### Bug Fixes

- Fix "patch" version bump adding an extra increment during release ([#75](https://github.com/openmethane/setup-wrf/pull/75))
- Fix WRF output processing not waiting for files to be closed ([#77](https://github.com/openmethane/setup-wrf/pull/77))


## setup-wrf v0.7.2 (2026-02-20)

### Bug Fixes

- Fix run-wrf.sh sync_output being called multiple times during script failure ([#74](https://github.com/openmethane/setup-wrf/pull/74))


## setup-wrf v0.7.0 (2026-02-20)

### Improvements

- Add met_source_dir config option to source FNL data outside the run dir ([#72](https://github.com/openmethane/setup-wrf/pull/72))
- Run WRF outside the STORE_PATH if using run-wrf.sh and config.docker.full.json ([#73](https://github.com/openmethane/setup-wrf/pull/73))


## setup-wrf v0.6.0 (2026-02-16)

### Improvements

- When NCPUS is not specified, utilise as many cores as possible based on WRF computation guidance ([#70](https://github.com/openmethane/setup-wrf/pull/70))


## setup-wrf v0.5.0 (2026-01-27)

### ⚠️ Breaking Changes  ⚠️

- Replace poetry with uv for tool and dependency management ([#63](https://github.com/openmethane/setup-wrf/pull/63))

### Improvements

- Update and pin dependency versions for conda and uv ([#64](https://github.com/openmethane/setup-wrf/pull/64))
- Skip WRF processing if completed output already exists in STORE_PATH/wrf ([#67](https://github.com/openmethane/setup-wrf/pull/67))


## setup-wrf v0.4.2 (2025-10-15)

### Bug Fixes

- Fix failing GDAS download URLs ([#62](https://github.com/openmethane/setup-wrf/pull/62))


## setup-wrf v0.4.1 (2025-09-01)

### Improvements

- Replace prior.openmethane.org data URL with official public data store in S3 ([#61](https://github.com/openmethane/setup-wrf/pull/61))


## setup-wrf v0.4.0 (2025-08-24)

### Improvements

- Add au-test domain details ([#60](https://github.com/openmethane/setup-wrf/pull/60))


## setup-wrf v0.3.1 (2025-07-28)

### Bug Fixes

- Update RDA base URL to fix FNL downloads failing with 404 errors ([#58](https://github.com/openmethane/setup-wrf/pull/58))


## setup-wrf v0.3.0 (2025-01-24)

### Improvements

- Skip running WRF and MCIP if results already exist, unless FORCE_WRF env variable is "true" ([#55](https://github.com/openmethane/setup-wrf/pull/55))

### Trivial/Internal Changes

- [#56](https://github.com/openmethane/setup-wrf/pull/56)


## setup-wrf v0.2.0 (2025-01-12)

### Improvements

- Make SETUP_WRF_VERSION environment variable available inside the container ([#53](https://github.com/openmethane/setup-wrf/pull/53))

### Bug Fixes

- Fix actions incorrectly populating container image version ([#54](https://github.com/openmethane/setup-wrf/pull/54))


## setup-wrf v0.1.2 (2024-11-21)

### Improvements

- Adopt common release process from openmethane/openmethane

  Adopt common docker build workflow from openmethane/openmethane ([#52](https://github.com/openmethane/setup-wrf/pull/52))


## setup-wrf v0.1.1 (2024-09-24)

No significant changes.
