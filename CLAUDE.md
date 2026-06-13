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
- Package a release executable: `./scripts/package_release.sh false` (pass `true` to also bundle sample invoices). Builds via PyInstaller into `release/FishbowlInvoiceTool/` and zips it.

## Git Workflow (when working on a GitHub issue)

When the work is tied to a specific GitHub issue, always do the following before making any changes:

- **Start from an up-to-date base branch.** Check out the base branch (usually `main` unless another branch is explicitly provided) and pull the latest (`git checkout main && git pull`) before creating the new branch, so work branches off the current tip rather than a stale local copy.
- **Name the branch so it links to the issue in GitHub.** Include the issue number in the branch name (e.g. `28-native-config-management` or `issue-28-native-config-management`) so GitHub associates the branch and its PR with the issue. Then branch off the freshly pulled base (`git checkout -b <issue-number>-<short-description>`).

## Architecture

The app is composed of five collaborating classes wired together in `InvoiceAppController`:

- **`ArgumentProvider`** (`source/ArgumentProvider.py`) — parses CLI args. `--integration-test` flag enables headless mode (no GUI mainloop, no error popups, processes all invoices and exits) used by the integration test CI workflow.
- **`InvoiceAppFileIO`** (`source/InvoiceAppFileIO.py`) — all file I/O: reads invoice PDFs via PyPDF2 (one string per page), reads/writes `logs/debug.txt` and `logs/results.txt`, and parses the three config files in `Configs/` (`Sales_Reps.txt`, `Payment_Terms.txt`, `Cost_Criteria.txt`) into dicts/lists used by the processor.
- **`InvoiceProcessor`** (`source/InvoiceProcessor.py`) + **`processor_utilities.py`** — core parsing logic. `populate_invoice()` extracts header fields (order/PO number, date, customer, payment terms, sales rep) from page 1 via regex. `process_invoice()` walks the line-item table across all pages line-by-line, classifying each payment line as labor/shipping/material cost using the criteria/exclusions loaded from `Cost_Criteria.txt`, then `process_end_of_invoice()` reads sales tax and the listed total once it hits the `Total:Subtotal` marker. All currency values use `Decimal` (see `format_currency`, `DECIMAL_ZERO` in `source/constants.py`) to avoid float precision issues — never use `float` for cost values.
- **`Invoice`** (`source/Invoice.py`) — plain data holder for one invoice's fields plus `to_formatted_string()` for output.
- **`InvoiceAppDisplay`** (`source/InvoiceAppDisplay.py`) — tkinter GUI (`tk.Tk` subclass). Menu bar (File/Edit/View/Preferences) lets users edit the three config files (Edit menu) and view the log files (View menu) in a native `FileEditorWindow`, switch themes (`source/color_theme.py`) and fonts (`source/font_settings.py`). In integration-test mode, error popups are suppressed (`show_error_popup` checks `argument_provider.integration_test_mode`).
- **`FileEditorWindow`** (`source/FileEditorWindow.py`) — a `tk.Toplevel` window that displays one text file's contents, styled with the active theme/font. Editable mode (Edit menu, config files) shows a Save button that calls a `save_config_callback`; read-only mode (View menu, log files) disables editing and shows no Save button. File reads/writes go through `InvoiceAppFileIO` (`read_text_file`/`write_text_file`); the controller's `handle_save_config` persists edits and re-parses the affected config so changes take effect without a restart.
- **`InvoiceAppController`** (`source/InvoiceAppController.py`) — entry point glue. Constructs the other components, loads config files, and orchestrates `handle_process_invoice()`: read PDF -> populate invoice -> process invoice -> display output -> warn on total mismatch -> write to `logs/results.txt`. The relative file paths (`Configs/`, `Invoices/`, `logs/`) live in `source/constants.py` and are read directly by the components that need them (`InvoiceAppFileIO`, `InvoiceAppDisplay`).

## Key Conventions

- `__debug__`-gated code (debug log writing/reset, "Debug Log" menu item) is stripped in the PyInstaller release build (`python -O`), per `scripts/package_release.sh`.
- Config files (`Configs/*.txt`) use `*` as a comment-line prefix and are not committed to this repo — they come from the `automated-invoice-testing` submodule via `copy_resources.sh`.
- The integration test workflow runs `python main.py --integration-test` and diffs the produced `logs/results.txt` against `automated-invoice-testing/canonical_correct_results.txt`, so any change to invoice parsing/output formatting can break it — check that submodule's expected output if changing `Invoice.to_formatted_string()` or processing logic.

## Production-Grade Code Practices (SOLID / DRY)

When adding or modifying code, favor changes that keep components focused and substitutable rather than growing existing classes with unrelated responsibilities:

- **Single Responsibility** — Each class here already maps to one concern (file I/O, parsing, display, orchestration). New logic should go in the class that owns that concern, not bolted onto `InvoiceAppController`. If a method is doing two distinct jobs (e.g., parsing *and* formatting), split it.
- **Open/Closed** — Prefer extending behavior via new config-driven entries (`Cost_Criteria.txt`, `Payment_Terms.txt`, `Sales_Reps.txt`) or new theme/font entries (`color_theme.py`, `font_settings.py`) over adding new conditional branches to existing parsing/display methods. When a new cost category or invoice field type is needed, look for the existing list/dict-driven pattern (e.g., `labor_criteria`, `ALL_THEMES`) before adding `if/elif` chains.
- **Liskov Substitution** — `Theme` instances (`color_theme.py`) and any future strategy-style objects must remain drop-in interchangeable; don't special-case a specific theme/criteria object's identity in calling code.
- **Interface Segregation** — Pass only the specific criteria/paths/callbacks a class needs (as the constructors already do — e.g., `InvoiceProcessor` takes `labor_criteria`, `labor_exclusions`, `shipping_criteria` individually rather than the whole `InvoiceAppFileIO`). Avoid passing large "god objects" into constructors when a narrower dependency will do.
- **Dependency Inversion** — Components depend on `InvoiceAppFileIO` and config data passed in at construction time (see `InvoiceAppController.__init__`), not on global state. Shared file paths are centralized in `source/constants.py` and imported where needed rather than hardcoded inline; tests substitute behavior by mocking `open`/`os`/PyPDF2 calls rather than by injecting paths (see existing `tests/*_tests.py` for the mocking patterns already in use).
- **DRY** — Shared parsing helpers belong in `processor_utilities.py` (e.g., `format_currency`, `search_text_by_re`); shared constants belong in `constants.py`, `color_theme.py`, or `font_settings.py`. Before adding a new regex/lookup/formatting routine, check these modules for an existing equivalent.
- Add type hints and concise docstrings consistent with the existing style (see any method in `source/InvoiceProcessor.py` for the expected `Args:`/`Returns:` format), and add corresponding tests in `tests/` for any new branch or utility function.

## Unit Testing

Unit tests live in `tests/` and run under `pytest`. When writing or modifying them, follow the two principles below.

### Test one object in isolation

Every unit test exercises exactly **one** class or function (the "unit under test"). Replace **all** collaborating objects with mocks so a failure points unambiguously at the unit being tested — never let a unit test depend on the real behavior of another class, the filesystem, a PDF, or the GUI. Reuse the patterns already established in the suite rather than inventing new ones:

- **Mock injected collaborators with `MagicMock(spec=Collaborator)`** and pass them into the constructor. See the `mock_file_io` and `invoice_processor` fixtures in `tests/InvoiceProcessor_tests.py`, where `InvoiceProcessor` is built with a `MagicMock(spec=InvoiceAppFileIO)` so no real file I/O occurs. The `spec=` argument keeps the mock honest — it only allows attributes/methods the real class defines.
- **Mock module-level dependencies with `@patch` / `mock_open`.** For classes that call `os`, `open`, or PyPDF2 directly, patch those calls instead of touching the real filesystem — see `tests/InvoiceAppFileIO_tests.py` (e.g. `@patch("os.remove")`, `@patch("os.path.exists", ...)`, `mock_open`).
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
