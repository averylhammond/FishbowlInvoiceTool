---
paths:
  - "scripts/**"
---

# Release packaging and the installer

`scripts/package_release.sh` builds the payload; `scripts/installer.iss` turns it into
`FishbowlInvoiceTool_Setup.exe` with Inno Setup, and `.github/workflows/release.yml` publishes
both when a `v*` tag is pushed (see `rules/ci.md` for the workflow side).

`package_release.sh <populate_invoices>` takes `true`/`false` — whether to bundle sample
invoices. It creates its own fresh venv so only release dependencies are packaged, builds a
PyInstaller **onefile** executable named `AutoInvoiceProc`, and zips
`release/FishbowlInvoiceTool/`. On Windows with Inno Setup present it additionally builds the
installer; that step is skipped on Linux or when `ISCC.exe` is absent. It detects CI via `CI=true`
and skips the local-developer working-tree cleanup there.

The build compiles with **`python -OO`**, which is what strips the `__debug__`-gated code (debug
log writing/reset, the View menu's "Debug Log" item) from the release.

## Load-bearing installer details

Several things in the `.iss` exist for the in-app updater and must not be "simplified":

- **`/RELAUNCH=1` is what brings the app back after a silent upgrade.** The interactive `[Run]`
  entry is flagged `skipifsilent`, so a `/VERYSILENT` install — which is how the updater invokes
  it — would otherwise finish with the application simply gone. A second `[Run]` entry gated on
  the `WantsRelaunch` `[Code]` function (`{param:relaunch|0} = '1'`) relaunches it, and only for
  that route: a hand-run silent install still springs no window open. Do not drop `skipifsilent`
  from the first entry.
- **`CloseApplications=force` is what makes the silent upgrade actually apply.** The running app
  launches the installer and exits, but Restart Manager scans a few hundred milliseconds later and
  asks the app to close by posting to its window — and a PyInstaller onefile build has two
  processes, the bootloader and its child, the bootloader owning no window. It never answers,
  Setup waits out its 30-second timeout, and because the updater passes `/SUPPRESSMSGBOXES` the
  resulting Abort/Retry/Ignore prompt defaults to **Abort**: the upgrade rolls back silently and
  the user is left on the old version with no error. No delay on the app's side fixes this, since
  there is no window to close — Setup has to terminate the process. Do not weaken this to plain
  `CloseApplications=yes`.
- **Setup clears the inherited `_PYI_*` variables before relaunching the app.** The app is a
  onefile build, so its environment describes its extracted bundle; it launches the installer as a
  child process, which inherits those variables and would pass them to the relaunched app. Since
  PyInstaller 6.22.1 an app that starts with them set assumes it is a worker sub-process of a
  onefile parent and requires its parent process to be the same executable — it is Setup, so it
  refuses to start with "Security validation failure: parent process has different executable". An
  in-place upgrade keeps the same path, so nothing else tips it off. `InitializeSetup` in the
  `.iss` unsets them. The deeper fix belongs upstream in `fishbowl_common`'s `UpdateInstaller`,
  which should hand the installer a sanitized environment rather than its own; this one also
  covers users upgrading from an app version released before that lands. Note
  `package_release.sh` leaves PyInstaller unpinned, which is how a bootloader change landed
  mid-release-series (see issue #99).
- **`PATCH_NOTES.md` ships in the payload and must be replaced on upgrade.**
  `package_release.sh` copies it next to `USER_GUIDE.txt`, and its `[Files]` entry is flagged
  plain `ignoreversion` — deliberately **not** the `onlyifdoesntexist uninsneveruninstall` the
  `Configs\*`/`Invoices\*` entries below it use. Those flags protect the customer's own data; this
  is app content, and a stale copy would have the app announce an update by showing the previous
  release's notes. There is also a `{group}\What's New` `[Icons]` entry beside the user guide's.
- **The silent upgrade needs no UAC prompt**, which is what makes the feature viable at all:
  `PrivilegesRequired=lowest` with `DefaultDirName={autopf}` resolves to
  `%LOCALAPPDATA%\Programs`, and the stable `AppId` GUID lets Inno upgrade in place without being
  told `/DIR`. `data/` has no `[Files]` entry and the input folders are flagged
  `uninsneveruninstall`, so settings, customer PDFs and configs all survive an upgrade. **Never
  change the `AppId`, and never share it with the sibling's.**
- `INSTALLER_ASSET_PATTERN` in `source/constants.py` must stay in step with the installer's
  `OutputBaseFilename` — the updater matches release assets by that name.

Neither the executable nor the installer is code-signed, so a manual download still draws a
SmartScreen warning. That matters more now that the app downloads and runs the installer itself;
an authenticode certificate is tracked as follow-up work.
