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

## Architecture

The app is composed of five collaborating classes wired together in `InvoiceAppController`:

- **`ArgumentProvider`** (`source/ArgumentProvider.py`) — parses CLI args. `--integration-test` flag enables headless mode (no GUI mainloop, no error popups, processes all invoices and exits) used by the integration test CI workflow.
- **`InvoiceAppFileIO`** (`source/InvoiceAppFileIO.py`) — all file I/O: reads invoice PDFs via PyPDF2 (one string per page), reads/writes `logs/debug.txt` and `logs/results.txt`, and parses the three config files in `Configs/` (`Sales_Reps.txt`, `Payment_Terms.txt`, `Cost_Criteria.txt`) into dicts/lists used by the processor.
- **`InvoiceProcessor`** (`source/InvoiceProcessor.py`) + **`processor_utilities.py`** — core parsing logic. `populate_invoice()` extracts header fields (order/PO number, date, customer, payment terms, sales rep) from page 1 via regex. `process_invoice()` walks the line-item table across all pages line-by-line, classifying each payment line as labor/shipping/material cost using the criteria/exclusions loaded from `Cost_Criteria.txt`, then `process_end_of_invoice()` reads sales tax and the listed total once it hits the `Total:Subtotal` marker. All currency values use `Decimal` (see `format_currency`, `DECIMAL_ZERO` in `source/globals.py`) to avoid float precision issues — never use `float` for cost values.
- **`Invoice`** (`source/Invoice.py`) — plain data holder for one invoice's fields plus `to_formatted_string()` for output.
- **`InvoiceAppDisplay`** (`source/InvoiceAppDisplay.py`) — tkinter GUI (`tk.Tk` subclass). Menu bar (File/Edit/View/Preferences) lets users open config/log files in the system editor (`source/platform_utils.py`), switch themes (`source/color_theme.py`) and fonts (`source/font_settings.py`). In integration-test mode, error popups are suppressed (`show_error_popup` checks `argument_provider.integration_test_mode`).
- **`InvoiceAppController`** (`source/InvoiceAppController.py`) — entry point glue. Defines all relative file paths (`Configs/`, `Invoices/`, `logs/`), constructs the other components, loads config files, and orchestrates `handle_process_invoice()`: read PDF -> populate invoice -> process invoice -> display output -> warn on total mismatch -> write to `logs/results.txt`.

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
- **Dependency Inversion** — Components depend on `InvoiceAppFileIO` and config data passed in at construction time (see `InvoiceAppController.__init__`), not on hardcoded paths or global state. Keep new file paths and external dependencies injected through constructors so tests can substitute fakes/mocks (see existing `tests/*_tests.py` for the mocking patterns already in use).
- **DRY** — Shared parsing helpers belong in `processor_utilities.py` (e.g., `format_currency`, `search_text_by_re`); shared constants belong in `globals.py`, `color_theme.py`, or `font_settings.py`. Before adding a new regex/lookup/formatting routine, check these modules for an existing equivalent.
- Add type hints and concise docstrings consistent with the existing style (see any method in `source/InvoiceProcessor.py` for the expected `Args:`/`Returns:` format), and add corresponding tests in `tests/` for any new branch or utility function.
