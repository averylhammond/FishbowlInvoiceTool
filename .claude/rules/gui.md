---
paths:
  - "source/gui/**"
---

# GUI conventions

Only two windows live in this repo. **Everything else themed comes from `fishbowl_common.gui`** —
do not re-add a local copy of a shared window; fix or extend it upstream and bump the pin in
`requirements/release.txt`.

## What comes from `fishbowl_common.gui`

| Name | Role |
| --- | --- |
| `ThemedSubwindow` | `tk.Toplevel` base: snapshots theme/font at open time, `_center_over_parent()` |
| `MessageWindow` | Themed replacement for `tkinter.messagebox`, centered over the app |
| `AboutWindow` | App name + version, both injected |
| `FileEditorWindow` | One text file, editable (Save button + callback) or read-only |
| `UpdateWindow` | "Exit and Update" / optional "Update and Restart" |
| `PatchNotesWindow` | Heading, notes in a read-only `ScrolledText`, Close |
| `Tooltip` | Hover text for widgets |
| `Theme`, `RED`, `ALL_THEMES`, `THEME_BY_NAME`, `FONT_FAMILIES`, `FONT_SIZES`, `DEFAULT_*` | Styling data |

All of it is re-exported from `fishbowl_common.gui`, so import from that one name rather than the
individual modules. That import is **separate** from the top-level `fishbowl_common`, which stays
tkinter-free so a headless run never loads tkinter — the split is what the `[gui]` extra in the
`requirements/release.txt` pin marks.

`AboutWindow`, `PatchNotesWindow` and `UpdateWindow` are application-agnostic and take everything
app-specific by injection: `handle_about()` passes `APP_NAME` and `VERSION` from
`source/constants.py`, and `show_patch_notes()` takes the name, version and notes from the
controller and adds only the current theme/font. `PatchNotesWindow` takes the notes as a
**string**, not a path — they are frequently several releases' sections concatenated — which is
why it is not a `FileEditorWindow(editable=False)`.

## `InvoiceAppDisplay`

The `tk.Tk` root. Body: title label, file entry + Browse, and the Process This Invoice / Process
All Invoices / Discover Invoices / Exit buttons over a `ScrolledText` output box. Menu bar:

- **File** — Open, Clear, Exit
- **Edit** — Cost Criteria / Payment Terms / Sales Reps, each opening an editable
  `FileEditorWindow` whose Save routes to the controller's `handle_save_config`
- **View** — Results Log, and **Debug Log only under `__debug__`** (stripped from the release
  build, which compiles with `python -OO`), both read-only
- **Preferences** — Theme, Font, Font Size cascades built from `ALL_THEMES` / `FONT_FAMILIES` /
  `FONT_SIZES`; each selection persists through `save_settings_callback`
- **Help** — About, Check for Updates, Open User Guide, What's New

Rules for this class:

- **It reads and writes no files and holds no version of its own.** Reads go through
  `read_file_callback`, writes through `save_config_callback`, and the version and patch notes
  arrive as arguments from the controller. `handle_view_patch_notes()` just calls
  `view_patch_notes_callback`.
- **It knows nothing about headless mode.** A headless run never constructs it — the controller
  returns into `run_integration_test()` before importing this module (#84) — so no popup path
  checks for integration-test mode, and none should. That is also what keeps `show_popup()` and
  `show_update_available()` identical to the sibling's, as a shared base class needs.
- **The display's whole share of the in-app update is forwarding a callback.** It never downloads
  or executes anything: `show_update_available()` passes `start_install` straight through to
  `UpdateWindow` as `start_install_callback`. When it is `None` — no matching installer asset, no
  checksums asset, or a non-Windows platform — the window falls back to the browser-only "Exit and
  Update" it has always offered. Both routes exit through `close_app_callback`, which is
  `self.handle_exit` — `self` is the root, so that closes the app and releases the executable's
  file lock for the installer.
- **Every way out routes through `handle_exit()`** — the Exit button, File -> Exit, the window's
  close box (bound with `protocol("WM_DELETE_WINDOW", …)` in `build_widgets()`) and the update
  window. It saves `winfo_geometry()` under `SETTING_KEY_GEOMETRY`, then calls `destroy()` (never
  `quit()`, which only ends `mainloop()` and leaves the window alive). Geometry is saved **on
  exit, deliberately not on `<Configure>`**, so dragging the window does not write to the
  settings database every frame. On startup `_parse_geometry()` checks the stored value against
  `GEOMETRY_PATTERN` and falls back to the default, since `geometry()` raises on a corrupt string.
- **Theme and font changes reconfigure existing widgets in place** (`apply_theme`,
  `apply_font_family`, `apply_font_size`, `_apply_font`, `_refresh_tooltips`) rather than
  rebuilding the window. A new widget must be added to those methods too, or it keeps the old
  styling until restart. Already-open subwindows keep the theme they snapshotted.
- **Add a new theme or font upstream**, as data in `fishbowl_common.gui` — the menus are built by
  iterating those collections, so nothing here needs a new branch.
- **Widgets are declared, not defaulted to `None`.** The `# fmt:off` block in `__init__` carries a
  bare `self.x: tk.Y` per widget, with no value: `build_widgets()` is the last statement in the
  constructor and creates every one of them, so nothing can observe one unset and no method guards
  against `None`. A new widget goes in that block *and* in `build_widgets()`. `InvoiceDiscoveryWindow`
  follows the same rule.
- **`# fmt:off` stops the formatter, not the linter.** `ruff format` honors it (including this
  repo's no-space spelling), so the aligned blocks survive untouched — but `ruff check` still
  reads every line inside one. An aligned line over the 120-column limit is wrapped onto a second
  comment line at the same column, as three of the field comments in `invoice.py` are — not
  suppressed with `# noqa: E501`.
- **`PLR0915` is off repo-wide**, in `pyproject.toml` rather than at `build_widgets()`: widget
  construction is one statement per widget, so the count tracks how many widgets the window has
  and splitting on it would scatter the layout without simplifying anything. Whether
  `build_widgets()` should be split for its own sake is issue #145.
- **`process_callback` is typed by the `ProcessInvoiceCallback` Protocol**, not a `Callable`: the
  call sites pass `append_output` by keyword, which `Callable[[Path, bool], None]` cannot express.
  The other callbacks are called positionally and stay plain `Callable`s.
- **Processing runs on a worker thread, not the GUI thread (#36).** Process This Invoice calls
  `process_callback` and Process All Invoices calls `process_all_callback`, and both return
  immediately. The loop over `Invoices/` lives in the controller, not here. While a run is in
  progress the controller calls **`set_processing(busy)`**, which locks both process buttons
  (no overlapping runs), Discover Invoices (it copies into the folder being processed) and the
  Edit menu's three config editors (their Save reloads criteria the run is reading in place).
  Exit, File, View, Preferences and Help stay live. **Every display method the worker needs
  reaches this class through the controller's `_on_gui_thread()`, never directly** — Tk is not
  thread-safe. A new display call made during processing must go the same way.

## `InvoiceDiscoveryWindow`

A `ThemedSubwindow` letting the user copy downloaded invoice PDFs into `Invoices/` without leaving
the app: browse (repeatedly, accumulating into `pending_files`), copy, and a running status area
reporting each outcome. Its `copy_callback` is `InvoiceAppFileIO.copy_invoice_file`, which returns
`"copied"`, `"exists"` or `"error"` — `"exists"` is what drives the overwrite confirmation.

It subclasses a shared base but **stays app-specific by decision** (issue #105): it is coupled to
this app's single-input-folder workflow, so it was deliberately not generalized and moved
upstream.

## Opening a window at startup

**Anything opened before the main loop is running must go through `display.after(0, …)`, never
inline.** `ThemedSubwindow._center_over_parent()` reads the parent's geometry, which is
`1x1+0+0` until the root window has been mapped, so an inline call lands the window in the corner
of the screen instead of over the app. This is why `show_patch_notes_if_updated()` schedules
rather than calls.
