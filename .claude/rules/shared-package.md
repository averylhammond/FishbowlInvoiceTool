---
paths:
  - "source/invoice_app_controller.py"
  - "source/constants.py"
  - "requirements/**"
---

# The shared package, updates and patch notes

`fishbowl-common` is a **pinned git dependency** in `requirements/release.txt`
(`fishbowl-common[gui] @ git+…@vX.Y.Z`), never a path or a submodule, so a change there is
invisible here until the pin moves. Its classes are application-agnostic and take **every**
app-specific value by constructor injection — that is the contract to preserve when touching this
wiring. Definitions and their tests live in that repo; do not duplicate either here.

| Class | Injected from here |
| --- | --- |
| `ArgumentProvider` | — (parses `--integration-test`) |
| `SettingsRepository` | `SETTINGS_DB_PATH` as `db_path` |
| `UpdateCoordinator` | `VERSION`, `GITHUB_REPO`, `display`, `INSTALLER_ASSET_PATTERN` as `asset_pattern` |
| `PatchNotes` | `PATCH_NOTES_PATH` as `notes_path` |
| `compare_versions()` | — (helper) |

`UpdateCoordinator` owns the **whole** update feature: the daemon worker thread, the
`UpdateChecker` fetch, the `display.after(0, …)` hop back onto the GUI thread, the download,
digest verification and silent detached launch of the installer, and the choice between opening
`UpdateWindow` and popping "No Updates Available" / "Update Check Failed". It takes its display as
a `typing.Protocol`, which is why it lives in the headless half of the package;
`InvoiceAppDisplay` satisfies it through `after()`, `show_update_available()` and `show_popup()`.
**Only the wiring is tested here** — the threading and result handling are covered upstream.

`INSTALLER_ASSET_PATTERN` names this app's installer among a release's assets; the shared package
cannot know it, since each Fishbowl app names its own. It must stay in step with
`installer.iss`'s `OutputBaseFilename`.

## Construction and gating in `InvoiceAppController`

**Headless is structural, not gated (#84)** — the same shape as `FishbowlInventoryTool`.
`__init__` builds only the headless half: `ArgumentProvider`, `InvoiceAppFileIO`,
`InvoiceProcessor`. `display`, `settings_repository`, `update_coordinator` and `patch_notes`
start as `None`. `start_application()` checks `integration_test_mode` **first** and returns
early into `run_integration_test()`. Only after that check does it import `InvoiceAppDisplay`
(a function-local import; the module-level one is under `TYPE_CHECKING`) and build the
`SettingsRepository`, the display, the `UpdateCoordinator` and `PatchNotes`. So a headless run
imports no tkinter, opens no database (no `data/` is left behind), touches no network and reads
no notes. Keep anything GUI-only below that early return rather than reintroducing a flag check.

**Configs are parsed in `_prepare_run()`, not `__init__`** — it also resets the log files. Each
branch calls it **after** wiring `report_error`, so a parse failure reaches the user. In the GUI
branch the file I/O controller's reporter is `partial(self._on_gui_thread,
self.display.show_popup)` rather than the bare method, because it also fires on the processing
worker thread; the settings repository's only fires on the GUI thread and stays direct.
`run_integration_test()` wires the file I/O reporter to `print` instead.

**Processing reports through two hooks, never `self.display` directly:** `show_message(title,
message)` and `show_output(invoice, append_output)`. The GUI branch points them at
`display.show_popup` / `display.display_invoice_output` through `_on_gui_thread()`. They default
to **silent no-ops**, and the headless run deliberately keeps that: those messages carry order
numbers, totals and file paths from the private submodule, which must never reach a CI log.
Only file I/O errors (paths and OS errors) go to stdout.

## Processing off the GUI thread (#36)

The same shape as `UpdateCoordinator`'s check. The display's two process callbacks,
`handle_process_invoice()` and `handle_process_all_invoices()`, each hand a job to
`_start_processing()`. That calls `display.set_processing(True)` on the GUI thread and starts a
`daemon=True` thread on `_run_processing()`. The thread runs the job, turns any unexpected
exception into a "Processing Error" popup (the `--noconsole` build would otherwise swallow it),
and in `finally` unlocks the controls.

The work itself is `process_invoice()` and `process_all_invoices()`. Every display call inside
them goes through **`_on_gui_thread(func, *args, **kwargs)`**: on the main thread it calls `func`
inline, and on any other thread it posts `partial(func, …)` through `display.after(0, …)`.
The headless run has no display at all, so it never reaches `_on_gui_thread()`: its hooks are
the silent defaults. It must still stay **synchronous**: `run_integration_test()` calls
`process_all_invoices()` directly, on the main thread. Do not route it through the worker.

`process_all_invoices()` iterates `file_io_controller.list_invoice_files()`, which owns the
directory walk, the `.pdf` filter and the **explicit sort by filename**. The integration diff
depends on that order, and bare `iterdir()` order is not guaranteed across platforms.

## Patch notes on the first launch after an update

The app updates itself silently, so the user comes back to a window indistinguishable from the one
they left. `PatchNotes` plus `SETTING_KEY_LAST_SEEN_VERSION` are what tell them what they got.

`show_patch_notes_if_updated()` **stamps `VERSION` first, then decides** — that ordering is what
makes an update's notes appear once rather than on every launch after it. It then shows nothing
unless the stored version is strictly **older** (`compare_versions(...) < 0`), and passes the whole
range to `notes_since(VERSION, last_seen_version)` so a user who skipped a release still sees what
they missed. Nothing is shown on a fresh install (nothing stored), an ordinary relaunch, or a
downgrade — nor on the first launch after upgrading *into* this feature, since a build that never
wrote the key is indistinguishable from a fresh install.

The window is opened through **`display.after(0, …)`, never inline** — see the startup rule in
`rules/gui.md`.

`handle_view_patch_notes()` is the Help → What's New callback and shows every section up to
`VERSION` (`notes_since(VERSION, None)`), since a user who dismissed the notes has no other way
back. Unlike the silent startup check it **reports when there is nothing to show** — the same
manual-versus-automatic split `handle_check_for_updates()` makes with `start(manual=True)`.

## Adding a constant

Paths in `source/constants.py` are relative to the executable's working directory and suffixed
`_DIR` for directories, `_PATH` for files — matching the sibling so the two stay recognisable.
Compose file paths from the base directory constants rather than rebuilding them. Note
`constants.py` is omitted from coverage in `pyproject.toml`, so it must hold no logic.
