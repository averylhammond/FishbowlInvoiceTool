# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

> **Keep the guidance current.** Whenever you change the architecture — add/remove/rename a class
> or module, move a responsibility between this repo and `fishbowl-common`, change a public
> signature, or alter the build/test/release workflow — update **this file or the matching
> `.claude/rules/` file** in the same change. Treat that as part of the definition of done for any
> structural change, not an afterthought.

## Project Overview

A Python/tkinter desktop app that parses Fishbowl-generated invoice PDFs and computes
labor/material/shipping cost breakdowns and totals, comparing the calculated total against the
listed total to catch Fishbowl's floating-point rounding errors. The input files in `Configs/`
determine which sales representative generated each invoice, which payment method was agreed upon,
and how each itemized line breaks into categories.

It is one of two Fishbowl desktop tools. The sibling is
[FishbowlInventoryTool](https://github.com/averylhammond/FishbowlInventoryTool); the shared
infrastructure and GUI package both depend on is
[fishbowl-common](https://github.com/averylhammond/fishbowl-common).

## Setup

- Submodule `automated-invoice-testing` provides sample invoices/configs for development and
  integration testing: `git submodule update --init`
- **This submodule repo is private since it contains sensitive customer data. Never commit
  information obtained from it, and never echo its contents into a CI log.**
- `./scripts/copy_resources.sh` copies sample `Configs/` and `Invoices/` from the submodule into
  the project root (required before running the app or integration tests locally).
- Virtual env: `python -m venv venv`, then `source venv/Scripts/activate` (Windows) or
  `source venv/bin/activate` (Linux/Mac).
- Install deps: `pip install -r requirements/dev.txt` (pulls in `release.txt` plus
  pytest/pytest-cov). CI pins Python `3.11.9`.

## Common Commands

- Run the app (GUI): `python main.py`
- Run the app headless (processes all invoices in `Invoices/` and writes `logs/results.txt`, no
  GUI): `python main.py --integration-test`
- Run all unit tests: `pytest tests/`
- Run a single test file: `pytest tests/test_Invoice.py`
- Run a single test:
  `pytest tests/test_processor_utilities.py::test_search_text_by_re_order_number_correct_format`
- Run with coverage (matches CI): `pytest --cov=./ --cov-report=xml tests/` — the 90% gate is
  `fail_under` in `pyproject.toml`, so it applies locally too
- Package a release: `./scripts/package_release.sh false` (pass `true` to also bundle sample
  invoices). Builds via PyInstaller into `release/FishbowlInvoiceTool/` and zips it; on Windows
  with Inno Setup installed it also builds `release/FishbowlInvoiceTool_Setup.exe`.

## CI

Four workflows in `.github/workflows/`: unit tests and code coverage on `ubuntu-latest`,
integration tests and releases on `windows-latest`. Coverage is gated at **90%**. The integration
check diffs `logs/results.txt` against the submodule's `canonical_correct_results.txt`, so any
change to parsing or output formatting breaks it until that canonical file is updated.

Pushing a `v*` tag runs the release workflow, which refuses the tag unless it matches
`constants.VERSION` **and** `PATCH_NOTES.md` has a matching `## <VERSION>` section. **Cutting a
release is: bump `VERSION`, add that version's `PATCH_NOTES.md` section, merge, then push a
matching `vX.Y.Z` tag.** Details in `.claude/rules/ci.md`.

## Architecture

`InvoiceAppController` constructs and wires everything. Each module owns exactly one concern:

| Module | Owns |
| --- | --- |
| `source/InvoiceAppController.py` | Entry-point glue: builds the collaborators, loads configs, orchestrates `handle_process_invoice()` (read PDF → populate → process → display → warn on total mismatch → write `logs/results.txt`) |
| `source/InvoiceAppFileIO.py` | All file I/O: invoice PDFs via pypdf (one string per page), the `logs/` files, copying invoices in, and parsing the three `Configs/` files |
| `source/InvoiceProcessor.py` | Parsing: `populate_invoice()` for header fields, `process_invoice()` for the line-item table, `process_end_of_invoice()` for tax and listed total |
| `source/processor_utilities.py` | Shared parsing helpers (`search_text_by_re`, `find_sales_rep`, `format_currency`, …) |
| `source/Invoice.py` | Plain data holder for one invoice, plus `to_formatted_string()` |
| `source/constants.py` | Paths, `APP_NAME`/`VERSION`/`GITHUB_REPO`, setting keys, `DECIMAL_ZERO` |
| `source/gui/InvoiceAppDisplay.py` | The `tk.Tk` root: main window and the File/Edit/View/Preferences/Help menu bar |
| `source/gui/InvoiceDiscoveryWindow.py` | Copying downloaded invoice PDFs into `Invoices/` without leaving the app |

**Everything else is `fishbowl-common`, taken as a pinned git tag.** From the headless half:
`ArgumentProvider`, `SettingsRepository`, `UpdateCoordinator`, `PatchNotes`, `compare_versions()`.
From `fishbowl_common.gui`: `ThemedSubwindow`, `MessageWindow`, `AboutWindow`, `FileEditorWindow`,
`UpdateWindow`, `PatchNotesWindow`, `Tooltip`, and the theme/font data. Those two imports are
deliberately separate — the top-level package stays tkinter-free so a headless run never loads
tkinter, which is what the `[gui]` extra in the pin marks.

The shared classes are application-agnostic and take every app-specific value by constructor
injection. **They lived in `source/gui/` until they were consolidated upstream; do not re-add a
local copy** — fix or extend them in `fishbowl-common` and bump the pin. Their tests live upstream
too, and deliberately have no counterpart here.

Two responsibilities worth knowing before touching them:

- **`UpdateCoordinator` owns the whole update feature** — the background check, the download,
  digest verification, and the silent in-place install. The display's entire share of it is
  forwarding a callback; it never downloads or executes anything.
- **`InvoiceDiscoveryWindow` stays app-specific by decision** (issue #105): it is coupled to this
  app's single-input-folder workflow, so it was deliberately not generalized and moved upstream.

## Key Conventions

- **All currency values are `Decimal`** (`format_currency`, `DECIMAL_ZERO`) — never `float` for a
  cost value. Catching floating-point rounding errors is the point of the app.
- `__debug__`-gated code (debug log writing/reset, the "Debug Log" menu item) is stripped from the
  release build, which compiles with **`python -OO`** per `scripts/package_release.sh`.
- Config files (`Configs/*.txt`) use `*` as a comment-line prefix and are **not committed** — they
  come from the `automated-invoice-testing` submodule via `copy_resources.sh`.
- Prefer extending behavior through config entries (`Cost_Criteria.txt`, `Payment_Terms.txt`,
  `Sales_Reps.txt`) or new theme/font data upstream over adding `if/elif` branches to existing
  parsing and display methods.
- Pass a class only the narrow dependencies it needs — `InvoiceProcessor` takes `labor_criteria`,
  `labor_exclusions` and `shipping_criteria` individually rather than the whole
  `InvoiceAppFileIO`. Avoid god objects in constructors.
- New logic goes in the class that owns that concern, not bolted onto `InvoiceAppController`. If a
  method is doing two distinct jobs (parsing *and* formatting), split it.
- Before adding a regex, lookup or formatting routine, check `processor_utilities.py`; before
  adding a themed window or widget helper, check `fishbowl_common.gui` — anything both Fishbowl
  tools need belongs there rather than in `source/gui/`.
- Add type hints and concise docstrings in the existing style (see any method in
  `source/InvoiceProcessor.py` for the expected `Args:`/`Returns:` format), and add tests in
  `tests/` for any new branch or utility function in the same change.
- **Every `def` in `source/` is fully annotated**: every parameter, and a return type on every
  function including `-> None`. Spell container types out — `list[str]`, `dict[str, str]` — since
  a bare `list` tells a reader (and a type checker) nothing. **The annotation is the only place a
  type is written**: under `source/`, an `Args:` entry is `name: description` and a `Returns:`
  block is the description alone, with no parenthesized or prefixed type repeating the signature.
  Under `tests/` the docstring type stays, since fixture and mock parameters are unannotated —
  see `.claude/rules/tests.md`.
- **Imports are grouped stdlib / third-party / first-party**, one blank line between groups,
  alphabetized within each. `fishbowl_common` is third party — it is installed from a pinned git
  tag — so it never sits among the `source.*` imports.

## Git Workflow (when working on a GitHub issue)

When the work is tied to a specific GitHub issue, always do the following before making changes:

- **Start from an up-to-date base branch.** Check out the base branch (usually `main` unless
  another is given) and pull (`git checkout main && git pull`) before creating the new branch, so
  work branches off the current tip rather than a stale local copy.
- **Name the branch so it links to the issue in GitHub.** Include the issue number (e.g.
  `28-native-config-management`), then branch off the freshly pulled base
  (`git checkout -b <issue-number>-<short-description>`).
- Merge through a PR, with a subject line ending `(closes #N)`.
- **A change to a public signature in `fishbowl-common` is not one PR but three**: the package
  first, then this repo's pin, then `FishbowlInventoryTool`.

## Where the rest of the guidance lives

Detail that only matters for part of the codebase lives in `.claude/rules/`, loaded when a
matching file is opened. Put new detail in the matching rule file rather than growing this one.

| File | Loads when you touch | Carries |
| --- | --- | --- |
| `rules/invoice-processing.md` | `InvoiceProcessor.py`, `processor_utilities.py`, `InvoiceAppFileIO.py`, `Invoice.py` | The parse pipeline, the `Decimal` rule, config file formats, error-reporting contract |
| `rules/gui.md` | `source/gui/**` | Window catalogue, menu structure, headless popup gate, theme/font reconfiguration, the `after(0, …)` startup rule |
| `rules/shared-package.md` | `InvoiceAppController.py`, `constants.py`, `requirements/**` | What each shared class takes by injection, construction order, integration-test gating, patch-notes logic |
| `rules/tests.md` | `tests/**` | Fixtures, patch targets, the tkinter-free `display` fixture, FIRST, banner and docstring conventions |
| `rules/ci.md` | `.github/workflows/**` | Workflow internals, the coverage gate, the two release gates, submodule handling |
| `rules/packaging.md` | `scripts/**` | `package_release.sh`, and the load-bearing `installer.iss` details the in-app updater depends on |
