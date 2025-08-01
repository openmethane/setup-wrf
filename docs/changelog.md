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

## setup-wrf v0.3.1 (2025-07-28)

### Bug Fixes

- Update RDA base URL to fix FNL downloads failing with 404 errors ([#58](https://github.com/openmethane/setup-wrf/pulls/58))


## setup-wrf v0.3.0 (2025-01-24)

### Improvements

- Skip running WRF and MCIP if results already exist, unless FORCE_WRF env variable is "true" ([#55](https://github.com/openmethane/setup-wrf/pulls/55))

### Trivial/Internal Changes

- [#56](https://github.com/openmethane/setup-wrf/pulls/56)


## setup-wrf v0.2.0 (2025-01-12)

### Improvements

- Make SETUP_WRF_VERSION environment variable available inside the container ([#53](https://github.com/openmethane/setup-wrf/pulls/53))

### Bug Fixes

- Fix actions incorrectly populating container image version ([#54](https://github.com/openmethane/setup-wrf/pulls/54))


## setup-wrf v0.1.2 (2024-11-21)

### Improvements

- Adopt common release process from openmethane/openmethane

  Adopt common docker build workflow from openmethane/openmethane ([#52](https://github.com/openmethane/setup-wrf/pulls/52))


## setup-wrf v0.1.1 (2024-09-24)

No significant changes.
