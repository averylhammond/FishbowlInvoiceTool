# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python/tkinter desktop app that parses Fishbowl-generated invoice PDFs and computes labor/material/shipping cost breakdowns and totals, comparing the calculated total against the listed total to catch Fishbowl's floating-point rounding errors. The input files in the Configs/ folder determine which sales representative generated each invoice, which payment method was agreed upon, and instructions on how to break each itemized line into categories.

## Setup

- Submodule `automated-invoice-testing` provides sample invoices/configs for development and integration testing: `git submodule update --init`
- This submodule repo is private since it contains sensitive customer data. Never commit information from sources obtained in this repo to preserve customer privacy.
- `./scripts/copy_resources.sh` copies sample `Configs/` and `Invoices/` from the submodule into the project root (required before running the app or integration tests locally).
- Virtual env: `python -m venv venv`, then `source venv/Scripts/activate` (Windows) or `source venv/bin/activate` (Linux/Mac).
- Install deps: `pip install -r requirements/dev.txt` (pulls in `release.txt` plus pytest/pytest-cov).

## Common Commands

- Run the app (GUI): `python main.py`
- Run the app headless (processes all invoices in `Invoices/` and writes `logs/results.txt`, no GUI): `python main.py --integration-test`
- Run all unit tests: `pytest tests/*`
- Run a single test file: `pytest tests/Invoice_tests.py`
- Run a single test: `pytest tests/processor_utilities_tests.py::test_search_text_by_re_order_number_correct_format`
- Run with coverage (matches CI): `pytest --cov=./ --cov-report=xml tests/*`
- Package a release executable: `./scripts/package_release.sh false` (pass `true` to also bundle sample invoices). Builds via PyInstaller into `release/FishbowlInvoiceTool/` and zips it. On Windows with Inno Setup installed, it additionally builds `release/FishbowlInvoiceTool_Setup.exe` (via `scripts/installer.iss`); this step is skipped on Linux or when Inno Setup is absent.

## Release Packaging

`scripts/package_release.sh` builds the payload; `scripts/installer.iss` turns it into
`FishbowlInvoiceTool_Setup.exe` with Inno Setup, and `.github/workflows/release.yml` publishes both
when a `v*` tag is pushed. Three things there exist for the in-app updater and are load-bearing:

- **`/RELAUNCH=1` is what brings the app back after a silent upgrade.** The interactive `[Run]` entry
  is flagged `skipifsilent`, so a `/VERYSILENT` install — which is how the updater invokes it — would
  otherwise finish with the application simply gone. A second `[Run]` entry gated on the
  `WantsRelaunch` `[Code]` function (`{param:relaunch|0} = '1'`) relaunches it, and only for that
  route: a hand-run silent install still springs no window open. Do not "simplify" this by dropping
  `skipifsilent` from the first entry.
- **`release.yml` publishes `SHA256SUMS.txt`** alongside the zip and the installer, written with
  `sha256sum` from inside `release/` so the names in it are bare and match the asset names on the
  Release. The updater verifies the installer against it **before executing it**, so a release
  missing that asset offers only the manual download — which is the graceful degradation, not a
  failure. `INSTALLER_ASSET_PATTERN` in `source/constants.py` must stay in step with the installer's
  `OutputBaseFilename`.
- **The silent upgrade needs no UAC prompt**, which is what makes the feature viable at all:
  `PrivilegesRequired=lowest` with `DefaultDirName={autopf}` resolves to `%LOCALAPPDATA%\Programs`,
  and the stable `AppId` GUID lets Inno upgrade in place without being told `/DIR`. `data/` has no
  `[Files]` entry and the input folders are flagged `uninsneveruninstall`, so settings, customer
  PDFs and configs all survive an upgrade. Never change the `AppId`, and never share it with the
  sibling's.

Neither the executable nor the installer is code-signed, so a manual download still draws a
SmartScreen warning. That matters more now that the app downloads and runs the installer itself; an
authenticode certificate is tracked as follow-up work rather than being done here.

## Git Workflow (when working on a GitHub issue)

When the work is tied to a specific GitHub issue, always do the following before making any changes:

- **Start from an up-to-date base branch.** Check out the base branch (usually `main` unless another branch is explicitly provided) and pull the latest (`git checkout main && git pull`) before creating the new branch, so work branches off the current tip rather than a stale local copy.
- **Name the branch so it links to the issue in GitHub.** Include the issue number in the branch name (e.g. `28-native-config-management` or `issue-28-native-config-management`) so GitHub associates the branch and its PR with the issue. Then branch off the freshly pulled base (`git checkout -b <issue-number>-<short-description>`).

## Architecture

The app is composed of five collaborating classes wired together in `InvoiceAppController`:

- **`ArgumentProvider`** (from the shared **`fishbowl-common`** package, not `source/`) — parses CLI args. `--integration-test` flag enables headless mode (no GUI mainloop, no error popups, processes all invoices and exits) used by the integration test CI workflow.
  - Two other shared infrastructure classes also come from `fishbowl-common`: **`SettingsRepository`** (SQLite settings store — `InvoiceAppController` injects `SETTINGS_DB_PATH` as `db_path`) and **`UpdateCoordinator`** (the whole update-check feature — the daemon worker thread, the `UpdateChecker` fetch, the `display.after(0, …)` hop back onto the GUI thread, and the choice between opening `UpdateWindow` and popping "No Updates Available"/"Update Check Failed"; the controller injects `VERSION`, `GITHUB_REPO` and the display). The package is a pinned git dependency in `requirements/release.txt`; its classes are application-agnostic and take all app-specific values via constructor injection. See that repo for the class definitions and their tests.
    - `UpdateCoordinator` takes its display as a `typing.Protocol`, so it lives in the headless half of the package rather than `fishbowl_common.gui`; `InvoiceAppDisplay` satisfies it through `after()`, `show_update_available()` and `show_popup()`. `InvoiceAppController` builds it in `__init__` (after the display it reports through) and calls `start()` only in `start_application()`'s non-integration-test branch, so a headless run performs no network I/O; `handle_check_for_updates()` is the display's Help-menu callback and just forwards `start(manual=True)`. The threading and result-handling this repo used to own are covered by that class's own tests upstream — here only the wiring is tested.
    - **In-app update ("Update and Restart").** The controller also injects `INSTALLER_ASSET_PATTERN` (`source/constants.py`) as the coordinator's `asset_pattern`, naming this app's installer among a release's assets; the shared package cannot know it, since each Fishbowl app names its own installer. Given that asset and a published `SHA256SUMS.txt`, the coordinator downloads the installer, verifies its digest, launches it silently detached and reports back — `InvoiceAppDisplay.show_update_available()` receives that flow as a second `start_install` argument and forwards it to `UpdateWindow` as `start_install_callback`. **The display's whole share of the feature is forwarding that callback**; it never downloads or executes anything itself. When the argument is `None` — no matching installer asset, no checksums asset, or a non-Windows platform — the window silently falls back to the browser-only "Exit and Update" it has always offered, which is also where a failed download lands. Both routes exit through the same `close_app_callback`, so the app leaves the same way whichever one is taken.
- **`fishbowl_common.gui`** (the same package's GUI half) — the themed tkinter windows and styling data this app shares with the sibling `FishbowlInventoryTool`: `ThemedSubwindow`, `MessageWindow`, `AboutWindow`, `FileEditorWindow`, `UpdateWindow`, `Tooltip`, and the `color_theme`/`font_settings` data (`Theme`, `RED`, `ALL_THEMES`, `THEME_BY_NAME`, `FONT_FAMILIES`, `FONT_SIZES`, …). All of it is re-exported from `fishbowl_common.gui`, so a consumer imports from that one name rather than the individual modules. These lived in `source/gui/` until they were consolidated upstream; **do not re-add a local copy** — fix or extend them in `fishbowl-common` and bump the pin.
  - It is a **separate import** from the top-level package, which stays tkinter-free so a headless run never loads tkinter. That split is what the `[gui]` extra in the `requirements/release.txt` pin marks: `fishbowl-common[gui] @ git+…@v1.2.0`.
  - `AboutWindow` is application-agnostic, so it takes both the name and the version it displays by injection — `InvoiceAppDisplay.handle_about()` passes `APP_NAME` and `VERSION` from `source/constants.py`.
  - Their unit tests live upstream in `fishbowl-common/tests/gui/` and deliberately have **no counterpart here**; this repo tests only its own display classes and the wiring around the shared ones.
- **`InvoiceDiscoveryWindow`** (`source/gui/InvoiceDiscoveryWindow.py`) — a `ThemedSubwindow` subclass letting the user copy downloaded invoice PDFs into `Invoices/` without leaving the app. It subclasses a shared base but **stays app-specific by decision** (see issue #105): it is coupled to this app's single-input-folder workflow, so it was deliberately not generalized and moved upstream.
- **`InvoiceAppFileIO`** (`source/InvoiceAppFileIO.py`) — all file I/O: reads invoice PDFs via pypdf (one string per page), reads/writes `logs/debug.txt` and `logs/results.txt`, and parses the three config files in `Configs/` (`Sales_Reps.txt`, `Payment_Terms.txt`, `Cost_Criteria.txt`) into dicts/lists used by the processor.
- **`InvoiceProcessor`** (`source/InvoiceProcessor.py`) + **`processor_utilities.py`** — core parsing logic. `populate_invoice()` extracts header fields (order/PO number, date, customer, payment terms, sales rep) from page 1 via regex. `process_invoice()` walks the line-item table across all pages line-by-line, classifying each payment line as labor/shipping/material cost using the criteria/exclusions loaded from `Cost_Criteria.txt`, then `process_end_of_invoice()` reads sales tax and the listed total once it hits the `Total:Subtotal` marker. All currency values use `Decimal` (see `format_currency`, `DECIMAL_ZERO` in `source/constants.py`) to avoid float precision issues — never use `float` for cost values.
- **`Invoice`** (`source/Invoice.py`) — plain data holder for one invoice's fields plus `to_formatted_string()` for output.
- **`InvoiceAppDisplay`** (`source/gui/InvoiceAppDisplay.py`) — tkinter GUI (`tk.Tk` subclass). Menu bar (File/Edit/View/Preferences) lets users edit the three config files (Edit menu) and view the log files (View menu) in a native `FileEditorWindow`, switch themes and fonts (both from `fishbowl_common.gui`). In integration-test mode, popups are suppressed (`show_popup` checks `argument_provider.integration_test_mode`).
- **`FileEditorWindow`** (from `fishbowl_common.gui`) — a `tk.Toplevel` window that displays one text file's contents, styled with the active theme/font. Editable mode (Edit menu, config files) shows a Save button that calls a `save_config_callback`; read-only mode (View menu, log files) disables editing and shows no Save button. File reads/writes go through `InvoiceAppFileIO` (`read_text_file`/`write_text_file`); the controller's `handle_save_config` persists edits and re-parses the affected config so changes take effect without a restart.
- **`InvoiceAppController`** (`source/InvoiceAppController.py`) — entry point glue. Constructs the other components, loads config files, and orchestrates `handle_process_invoice()`: read PDF -> populate invoice -> process invoice -> display output -> warn on total mismatch -> write to `logs/results.txt`. The relative file paths (`Configs/`, `Invoices/`, `logs/`) live in `source/constants.py` and are read directly by the components that need them (`InvoiceAppFileIO`, `InvoiceAppDisplay`).

## Key Conventions

- `__debug__`-gated code (debug log writing/reset, "Debug Log" menu item) is stripped in the PyInstaller release build (`python -O`), per `scripts/package_release.sh`.
- Config files (`Configs/*.txt`) use `*` as a comment-line prefix and are not committed to this repo — they come from the `automated-invoice-testing` submodule via `copy_resources.sh`.
- The integration test workflow runs `python main.py --integration-test` and diffs the produced `logs/results.txt` against `automated-invoice-testing/canonical_correct_results.txt`, so any change to invoice parsing/output formatting can break it — check that submodule's expected output if changing `Invoice.to_formatted_string()` or processing logic.

## Production-Grade Code Practices (SOLID / DRY)

When adding or modifying code, favor changes that keep components focused and substitutable rather than growing existing classes with unrelated responsibilities:

- **Single Responsibility** — Each class here already maps to one concern (file I/O, parsing, display, orchestration). New logic should go in the class that owns that concern, not bolted onto `InvoiceAppController`. If a method is doing two distinct jobs (e.g., parsing *and* formatting), split it.
- **Open/Closed** — Prefer extending behavior via new config-driven entries (`Cost_Criteria.txt`, `Payment_Terms.txt`, `Sales_Reps.txt`) or new theme/font entries (upstream in `fishbowl_common.gui`) over adding new conditional branches to existing parsing/display methods. When a new cost category or invoice field type is needed, look for the existing list/dict-driven pattern (e.g., `labor_criteria`, `ALL_THEMES`) before adding `if/elif` chains.
- **Liskov Substitution** — `Theme` instances (from `fishbowl_common.gui`) and any future strategy-style objects must remain drop-in interchangeable; don't special-case a specific theme/criteria object's identity in calling code.
- **Interface Segregation** — Pass only the specific criteria/paths/callbacks a class needs (as the constructors already do — e.g., `InvoiceProcessor` takes `labor_criteria`, `labor_exclusions`, `shipping_criteria` individually rather than the whole `InvoiceAppFileIO`). Avoid passing large "god objects" into constructors when a narrower dependency will do.
- **Dependency Inversion** — Components depend on `InvoiceAppFileIO` and config data passed in at construction time (see `InvoiceAppController.__init__`), not on global state. Shared file paths are centralized in `source/constants.py` and imported where needed rather than hardcoded inline; tests substitute behavior by mocking `open`/`os`/pypdf calls rather than by injecting paths (see existing `tests/*_tests.py` for the mocking patterns already in use).
- **DRY** — Shared parsing helpers belong in `processor_utilities.py` (e.g., `format_currency`, `search_text_by_re`); shared constants belong in `constants.py`, and styling data upstream in `fishbowl_common.gui`. Before adding a new regex/lookup/formatting routine, check these modules for an existing equivalent — and before adding a themed window or widget helper, check `fishbowl_common.gui`, since anything both Fishbowl tools need belongs there rather than in `source/gui/`.
- Add type hints and concise docstrings consistent with the existing style (see any method in `source/InvoiceProcessor.py` for the expected `Args:`/`Returns:` format), and add corresponding tests in `tests/` for any new branch or utility function.

## Unit Testing

Unit tests live in `tests/` and run under `pytest`. When writing or modifying them, follow the two principles below.

### Test one object in isolation

Every unit test exercises exactly **one** class or function (the "unit under test"). Replace **all** collaborating objects with mocks so a failure points unambiguously at the unit being tested — never let a unit test depend on the real behavior of another class, the filesystem, a PDF, or the GUI. Reuse the patterns already established in the suite rather than inventing new ones:

- **Mock injected collaborators with `MagicMock(spec=Collaborator)`** and pass them into the constructor. See the `mock_file_io` and `invoice_processor` fixtures in `tests/InvoiceProcessor_tests.py`, where `InvoiceProcessor` is built with a `MagicMock(spec=InvoiceAppFileIO)` so no real file I/O occurs. The `spec=` argument keeps the mock honest — it only allows attributes/methods the real class defines.
- **Mock module-level dependencies with `@patch` / `mock_open`.** For classes that call `os`, `open`, or pypdf directly, patch those calls instead of touching the real filesystem — see `tests/InvoiceAppFileIO_tests.py` (e.g. `@patch("os.remove")`, `@patch("os.path.exists", ...)`, `mock_open`).
- **Construct the unit under test in a pytest fixture** (e.g. the `file_io` fixture) so each test starts from a clean, identically-configured object.
- **Name unasserted mock parameters with a leading underscore** (`_mock_os_exists`) and reserve plain names (`mock_os_remove`) for mocks you assert against — matching the existing files.

### Follow the FIRST principles

- **Fast** — No real file, PDF, or GUI I/O; mock it. The whole `pytest tests/*` run should stay quick.
- **Independent** — No ordering dependencies or shared mutable state between tests. Each test builds its own object via a fixture and asserts on its own data.
- **Repeatable** — Deterministic on every run and machine. Do not rely on the real filesystem, the clock, or the `automated-invoice-testing` submodule — that submodule drives the *integration* test (`python main.py --integration-test`), not unit tests.
- **Self-validating** — Each test asserts a clear pass/fail (`assert ... ==`, `assert_called_once_with(...)`). Never require manual inspection of `logs/` output to judge the result.
- **Timely** — Add or extend tests in `tests/` alongside any new branch or utility function, in the same change (reinforcing the final bullet of the SOLID/DRY section above).

### Conventions

Match the existing files: give each test a docstring describing what it verifies, with an `Args:` block documenting each mock/fixture parameter, and group tests for a given function under the `###`-bordered comment banners used throughout `tests/`.
