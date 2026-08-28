---
paths:
  - ".github/workflows/**"
  - "requirements/**"
---

# CI workflows

Four workflows live in `.github/workflows/`. All pin Python **3.11.9** (the coverage job pins
`3.11`) and install `requirements/dev.txt`.

| Workflow | Trigger | Runner | Does |
| --- | --- | --- | --- |
| `unit-tests.yml` | PRs to `main`, manual | `ubuntu-latest` | `pytest tests/` |
| `code-coverage.yml` | PRs to `main`, pushes to `main`, manual | `ubuntu-latest` | `pytest --cov` with a coverage gate, uploads to Codecov |
| `integration-tests.yml` | PRs to `main`, manual | `windows-latest` | Runs the app headless and diffs the output |
| `release.yml` | pushes of a `v*` tag | `windows-latest` | Verifies, tests, packages and publishes the release |

Notes that are easy to get wrong:

- **`unit-tests.yml` checks out into `project_directory`** and sets that as the job's
  `working-directory`, unlike the other three which check out at the root. Paths in that workflow
  are relative to it.
- **The coverage gate is `--cov-fail-under=90`**, which fails the job (and blocks the PR once the
  check is required in branch protection) whenever total coverage drops below 90%. The Codecov
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

## Release gates

`release.yml` fails the tag before building if either gate trips, both reported with `::error::`:

1. **Tag versus source version** — `${GITHUB_REF_NAME#v}` must equal `constants.VERSION`, so a
   release can never ship with an About box that disagrees with its tag.
2. **Patch notes must document the version** — `PATCH_NOTES.md` must contain a matching
   `^## v?<VERSION>( |$)` section. The app shows these notes on the first launch after an update,
   so a release missing its section would ship silently and only surface when a customer updated
   into it.

It then reruns the unit and integration tests against the tagged commit, `choco install
innosetup`, packages, and writes `SHA256SUMS.txt` with `sha256sum` **from inside `release/`** so
the names in it are bare and match the asset names on the Release. The updater verifies the
installer against that file **before executing it**, so a release missing that asset offers only
the manual download — graceful degradation, not a failure. The Release is created with
`gh release create --generate-notes` carrying the zip, the installer and the checksums.

**Cutting a release is therefore:** bump `VERSION` in `source/constants.py`, add that version's
`PATCH_NOTES.md` section, merge, then push a matching `vX.Y.Z` tag.
