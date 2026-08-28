# FishbowlInvoiceTool

[![Unit Tests](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml/badge.svg?branch=main)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/integration-tests.yml/badge.svg?branch=main)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/integration-tests.yml)
[![Code Coverage](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/code-coverage.yml/badge.svg?branch=main)](https://github.com/averylhammond/FishbowlInvoiceTool/actions/workflows/code-coverage.yml)
[![codecov](https://codecov.io/gh/averylhammond/FishbowlInvoiceTool/branch/main/graph/badge.svg)](https://codecov.io/gh/averylhammond/FishbowlInvoiceTool)

A Python desktop app (tkinter) that parses Fishbowl-generated invoice PDFs and computes
labor, material, and shipping cost breakdowns and totals, comparing the calculated total
against the listed total to catch Fishbowl's floating-point rounding errors. The
configuration files in `Configs/` determine which sales representative generated each
invoice, which payment method was agreed upon, and how each itemized line is broken into
cost categories.

## Setup

**1. Clone the repo** into a project folder.

**2. Initialize the test-data submodule.** Sample invoices and config files live in
[automated-invoice-testing](https://github.com/averylhammond/automated-invoice-testing),
which is wired in as a submodule:

```bash
git submodule update --init
```

> **Note:** this submodule is private because it contains sensitive customer data. Never
> commit data sourced from it back into this repo.

The resulting folder structure:

```
project_root/
└── FishbowlInvoiceTool/
    ├── scripts/copy_resources.sh
    └── automated-invoice-testing/
        └── resources/
```

**3. Stage the sample resources** so the app has invoices and configs to run against:

```bash
./scripts/copy_resources.sh
```

This adds:

```
FishbowlInvoiceTool/
├── Configs/
│   ├── Cost_Criteria.txt
│   ├── Payment_Terms.txt
│   └── Sales_Reps.txt
└── Invoices/
    ├── S0-12345.pdf
    ├── S0-98675.pdf
    └── ...
```

> **Note:** both folders are committed empty (a `.gitkeep` placeholder each) because
> their contents are customer data and stay gitignored. Run this step before the first
> launch — without the config files the app opens and reports a config error for each
> one it cannot read.

**4. Create and activate a virtual environment** (Python 3.11):

```bash
python -m venv venv
source venv/Scripts/activate   # Windows; use venv/bin/activate on Linux/Mac
```

**5. Install dependencies:**

```bash
pip install -r requirements/dev.txt      # release.txt plus pytest and pytest-cov
pip install -r requirements/release.txt  # runtime dependencies only
```

> **Note:** on Linux, `tkinter` is not part of the standard library install and must be
> installed separately, then the virtual environment reactivated:
>
> - Debian-based: `sudo apt-get install python3-tk`
> - Fedora: `sudo dnf install python3-tkinter`
> - Arch-based: `sudo pacman -S python3-tk`

## Usage

```bash
python main.py                    # run the GUI
python main.py --integration-test # run headless, writing logs/results.txt
```

Headless mode processes every invoice in `Invoices/` and exits without opening a window
or showing popups. It is what CI uses to validate output without GUI interaction.

See [`USER_GUIDE.txt`](USER_GUIDE.txt) for end-user instructions.

## Testing

```bash
pytest tests/                                        # unit tests
pytest --cov=./ --cov-report=term-missing tests/     # unit tests with a coverage table
```

Reproduce the integration test locally (after `./scripts/copy_resources.sh`):

```bash
python main.py --integration-test
diff logs/results.txt automated-invoice-testing/canonical_correct_results.txt
```

When invoice parsing or output formatting changes intentionally, regenerate
`canonical_correct_results.txt` in the `automated-invoice-testing` repo and bump the
submodule pointer.

## Continuous integration

All three CI workflows run on pull requests to `main` and on manual dispatch; the
coverage workflow additionally runs on pushes to `main` so Codecov records a baseline for
PR diffs.

| Workflow | What it checks |
| --- | --- |
| [Unit Tests](.github/workflows/unit-tests.yml) | `pytest tests/` on `ubuntu-latest`. |
| [Integration Tests](.github/workflows/integration-tests.yml) | Runs the app headless on `windows-latest` and fails unless `logs/results.txt` matches the submodule's `canonical_correct_results.txt`. Needs the `CUSTOMER_DATA_PAT` secret to check out the private submodule. |
| [Code Coverage](.github/workflows/code-coverage.yml) | `pytest --cov=./ --cov-report=xml --cov-fail-under=90 tests/`, uploaded to Codecov. Needs the `CODECOV_TOKEN` secret. |

## Releases

Package a release build locally:

```bash
./scripts/package_release.sh false   # pass true to also bundle sample invoices
```

This builds the executable with PyInstaller into `release/FishbowlInvoiceTool/` and zips
it. On Windows with [Inno Setup](https://jrsoftware.org/isinfo.php) installed it
additionally builds `release/FishbowlInvoiceTool_Setup.exe` from `scripts/installer.iss`;
that step is skipped on Linux or when Inno Setup is absent.

Pushing a `v*` tag runs the
[Release workflow](.github/workflows/release.yml), which verifies the tag matches
`VERSION` in `source/constants.py`, runs the unit and integration tests, packages the zip
and installer, and publishes them as a GitHub Release.

## Related projects

- [FishbowlInventoryTool](https://github.com/averylhammond/FishbowlInventoryTool) — the
  sibling desktop app, which parses Fishbowl inventory availability and turnover report
  PDFs into an Excel report.
- [fishbowl-common](https://github.com/averylhammond/fishbowl-common) — the shared
  infrastructure and GUI package both apps depend on. This app uses `ArgumentProvider`,
  `SettingsRepository`, `UpdateCoordinator`, `PatchNotes` and `compare_versions()` from its
  headless half, and the themed windows and theme/font data from `fishbowl_common.gui`.
