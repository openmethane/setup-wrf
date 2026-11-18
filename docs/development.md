
# Development

## Code review

Review isn't only for catching bugs. It keeps the team aware of how the
project is changing and builds agreement on decisions. Not every pull request
benefits from that. The author of a pull request decides whether it needs a
human review, and says so on the first line of the description, where it
shows up in email notifications:

```markdown
**Review:** needed — changes science outputs: WRF now runs one rank per physical core, which changes outputs at rounding level
```

```markdown
**Review:** not needed — patch dependency updates, CI passing; merging Thursday unless someone objects
```

Always give a reason. The reason lets everyone else check the decision at a
glance, and shows over time whether these categories need adjusting.

The lists below are a guide, not rules, and some judgement is still needed.
When a change doesn't clearly fit, ask: would the rest of the team want to
know about this, or have a say in it? If so, it needs review.

### Review needed

- **Changes to science outputs.** Any change to the meteorology setup-wrf
  produces, which MCIP turns into CMAQ's meteorological inputs, needs review,
  however small the fix that causes it. This includes changes to namelists,
  domains, input data (FNL, geography) and how WRF is run, if they change the
  values in the output files.
- **Refactors that change structure or behaviour across more than one file.**
- **New concepts or features**, including new data sources, domains, settings
  and methodology decisions.
- **Documentation changes.** If something is worth documenting, it's worth
  the rest of the team knowing about it and agreeing with it. This doesn't
  include fixes to typos, grammar or formatting, which are mechanical changes.
- **Changes that make a production run fail, or stop failing, where it didn't
  before.** This includes changes to the Docker image that production jobs
  depend on. Make sure whoever looks after production runs knows about these.

### Review not needed

- **Infrastructure changes** made by the person who looks after the
  infrastructure.
- **Mechanical changes**, such as small corrections and bug fixes whose
  correctness is established by tests, tool-generated changes such as
  running a formatter, and fixes to typos, grammar or formatting in
  documentation. Being mechanical is what matters here, not size: a
  formatter run that touches every file is still mechanical.
- **Minor or patch dependency updates.** Major version updates need review.
- **Small changes to logging, warnings, types and project settings.**

### Science code isn't the same as science outputs

A change can touch science code without changing any outputs. For example,
it can fix a crash in a path that never produced results, or make the run
fail on bad input instead of producing a bad file. These changes don't need
review, but the reason has to give the evidence that the outputs don't
change, not just say so. If you can't write that sentence, choose "needed".

### Not needed doesn't mean merged immediately

For a "not needed" pull request, say when you'll merge it. This gives
everyone a chance to ask for a review before then. Anyone can switch a pull
request to "needed", and then it waits for a review as usual.

### Examples

| Pull request | First line |
|---|---|
| [#87](https://github.com/openmethane/setup-wrf/pull/87) | **Review:** not needed — bug fix with tests; interrupted FNL downloads no longer leave truncated files, and complete downloads are unchanged |
| [#93](https://github.com/openmethane/setup-wrf/pull/93) | **Review:** not needed — security update to the trust stores (certifi and ca-certificates); no behaviour change |
| [#92](https://github.com/openmethane/setup-wrf/pull/92) | **Review:** needed — changes science outputs: one rank per physical core changes outputs at rounding level; three output settings are byte-identical |
| [#84](https://github.com/openmethane/setup-wrf/pull/84) | **Review:** needed — replaces the conda-based image with Debian packages and uv, and builds `wgrib2` from source |
| [#94](https://github.com/openmethane/setup-wrf/pull/94) | **Review:** needed — removes chamber from the image; production `wrf-run` jobs fail with this image until their job definitions stop calling chamber |

#94 is a six-line change to the Dockerfile and doesn't touch science code,
but production runs would fail if the image were released before the job
definitions were updated. That is why it needs review, or at least for
whoever looks after production runs to know about it.

## Docker images

A docker image will be built and made available through the GitHub Container
Registry for every push to `main` branch, as well as each PR.

See https://github.com/orgs/openmethane/packages for a list of available
packages.

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
