---
paths:
  - ".github/workflows/**"
  - "requirements/**"
---

# CI workflows

Five workflows live in `.github/workflows/`. All pin Python **3.11.9** (#98), cache pip against
`requirements/dev.txt`, and install that file, except the lint job — see below.

| Workflow | Trigger | Runner | Does |
| --- | --- | --- | --- |
| `unit-tests.yml` | PRs to `main`, manual | `ubuntu-24.04` | `pytest tests/` |
| `lint.yml` | PRs to `main`, manual | `ubuntu-24.04` | `ruff check` and `ruff format --check` |
| `code-coverage.yml` | PRs to `main`, pushes to `main`, manual | `ubuntu-24.04` | `pytest --cov` with a coverage gate, uploads to Codecov |
| `integration-tests.yml` | PRs to `main`, manual | `windows-latest` | Runs the app headless and diffs the output |
| `release.yml` | pushes of a `v*` tag | `windows-latest` | Verifies, tests, packages and publishes the release |

**The three Linux jobs pin `runs-on: ubuntu-24.04`.** `setup-python` installs an exact patch
version only from a prebuilt manifest, and that manifest has no 3.11.9 for Ubuntu 26.04 — so when
`ubuntu-latest` moved to 26.04, the pinned jobs failed at "Set up Python environment" before
running anything. Do not move any of them back to `ubuntu-latest` without also moving the Python
pin to a version the new image's manifest carries. FishbowlInventoryTool pins its Linux jobs the
same way.

**Every workflow sets `cache: 'pip'`** with `cache-dependency-path: requirements/dev.txt`. The
cache saves the PyPI downloads, but not the `fishbowl-common` clone: pip does not cache a wheel
built from a git tag, because a tag can move.

**The four non-release workflows share a concurrency group** of
`${{ github.workflow }}-${{ github.ref }}` with `cancel-in-progress: true`, so a newer push to a
PR cancels the run it supersedes. `release.yml` deliberately has none: cancelling a
half-finished release is worse than letting it run.

Notes that are easy to get wrong:

- **Only `release.yml` needs a write token** (`contents: write`, to publish the release).
  The other four declare `contents: read` — Codecov posts its PR comments through its own GitHub
  App, so coverage needs no write token either, and `integration-tests.yml` checks out the private
  submodule with `CUSTOMER_DATA_PAT` rather than `GITHUB_TOKEN`.
- **The coverage gate is `fail_under = 90` in `pyproject.toml`**, not a workflow flag, so a local
  `pytest --cov` enforces it too. `code-coverage.yml` runs `pytest --cov=source`, which names
  the measured package directly, so the `omit` list only drops the in-package files that are
  deliberately unmeasured. It fails the job (and blocks the PR once the check is required
  in branch protection) whenever total coverage drops below 90%. The Codecov
  upload step is `if: always()` so the report still lands when the gate fails — that is exactly
  when the PR comment is most useful. `CODECOV_TOKEN` is the repo upload token.
- **The two Windows workflows check out the private submodule** with
  `submodules: recursive` and `token: ${{ secrets.CUSTOMER_DATA_PAT }}`, then run
  `./scripts/copy_resources.sh`. `automated-invoice-testing` holds customer data — never echo its
  contents into a workflow log. The Ubuntu workflows need none of it, since unit tests touch no
  real files.
- **The integration check is a `diff`**, not an assertion suite: it runs
  `python main.py --integration-test` and compares `logs/results.txt` against the submodule's
  `canonical_correct_results.txt`. Any change to parsing or to `Invoice.to_formatted_string()`
  breaks it until that canonical file is updated in the submodule repo.
- Both Windows jobs set `defaults.run.shell: bash`, since every step is written in bash.
- **`lint.yml` installs only ruff**, via `pip install "$(grep '^ruff==' requirements/dev.txt)"`,
  rather than the whole of `dev.txt` like the other four. Linting needs neither pypdf nor
  fishbowl-common, and installing the latter clones a git dependency on every run. The version
  is still single-sourced from `dev.txt`, so CI and a developer's machine cannot drift.
- **The lint gate is the whole rule set**, not a subset: any `ruff check` finding or any
  formatting difference fails the job. The configuration, and the reason behind every
  suppression, lives in `[tool.ruff]` in `pyproject.toml`.

## Release gates

`release.yml` fails the tag before building if either gate trips, both reported with `::error::`:

1. **Tag versus source version** — `${GITHUB_REF_NAME#v}` must equal `constants.VERSION`, so a
   release can never ship with an About box that disagrees with its tag.
2. **Patch notes must document the version** — `PATCH_NOTES.md` must contain a matching
   `^## v?<VERSION>( |$)` section. The app shows these notes on the first launch after an update,
   so a release missing its section would ship silently and only surface when a customer updated
   into it.

It then reruns the unit and integration tests against the tagged commit, installs Inno Setup via
Chocolatey (pinned with `--version`, plus `--allow-downgrade` since `windows-latest` preinstalls
Inno Setup and an unconstrained install is a no-op on whatever the image carries), packages, and writes `SHA256SUMS.txt` with `sha256sum` **from inside `release/`** so
the names in it are bare and match the asset names on the Release. The updater verifies the
installer against that file **before executing it**, so a release missing that asset offers only
the manual download — graceful degradation, not a failure. The Release is created with
`gh release create --generate-notes` carrying the zip, the installer and the checksums.

**Cutting a release is therefore:** bump `VERSION` in `source/constants.py`, add that version's
`PATCH_NOTES.md` section, merge, then push a matching `vX.Y.Z` tag.
