---
paths:
  - "source/InvoiceAppController.py"
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

**This controller builds every collaborator, the display included, in `__init__`.** The sibling
`FishbowlInventoryTool` builds its GUI collaborators inside the non-integration-test branch and
gets "no database, no window" structurally — **do not copy that placement here.** Because
everything is built up front, anything that must not happen headlessly is gated **explicitly** on
`argument_provider.integration_test_mode`, in `start_application()`'s GUI branch:

- `update_coordinator.start()` — so a headless run performs no network I/O
- `show_patch_notes_if_updated()` — so it reads no notes and opens no window

Constructing `PatchNotes` and `UpdateCoordinator` in `__init__` is fine and deliberate:
constructing them reads nothing and touches no network; the file is read per call.

Order matters in `__init__`: `report_error` on the file I/O controller and the settings repository
is wired to `display.show_popup` **before** the config files are parsed, so parse failures reach
the user.

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
`constants.py` is omitted from coverage in `.coveragerc`, so it must hold no logic.
