---
paths:
  - "tests/**"
---

# Unit testing conventions

Unit tests live in `tests/`, one `tests/test_<ModuleName>.py` per module under `source/`. That
name matches pytest's default `python_files` pattern, so a bare `pytest` collects the whole
suite and the jobs in `.github/workflows/` invoke it as `pytest tests/` with no glob.
`tests/__init__.py` is empty but load-bearing: with it present, pytest's prepend import mode puts
the repo root on `sys.path`, which is what makes `from source... import` resolve. There is no
`conftest.py`; pytest and coverage configuration lives in `pyproject.toml`, whose coverage section
measures `./source` and omits `main.py`, `tests/`, the venvs, both `__init__.py` files and
`source/constants.py`, and whose `fail_under = 90` is the gate CI relies on. The two `__init__.py`
files are empty and `constants.py` holds no logic, so none of them has behaviour to measure.

`tests/test_InvoiceProcessor.py` (a class with injected collaborators) and
`tests/test_InvoiceAppDisplay.py` (the widget-patching fixture) are the two reference
implementations — mirror them rather than inventing new patterns.

## Test one object in isolation

Every unit test exercises exactly **one** class or function. Replace **all** collaborating
objects with mocks so a failure points unambiguously at the unit being tested — never let a unit
test depend on the real behavior of another class, the filesystem, a PDF, or the GUI.

- **Mock injected collaborators with `MagicMock(spec=Collaborator)`** and pass them into the
  constructor. See the `mock_file_io` and `invoice_processor` fixtures in
  `tests/test_InvoiceProcessor.py`, where `InvoiceProcessor` is built with a
  `MagicMock(spec=InvoiceAppFileIO)` so no real file I/O occurs. The `spec=` argument keeps the
  mock honest — it only allows attributes and methods the real class defines.
- **Mock module-level dependencies with `@patch` / `mock_open`.** For classes that call `os`,
  `open`, or pypdf directly, patch those calls instead of touching the real filesystem — see
  `tests/test_InvoiceAppFileIO.py` (e.g. `@patch("os.remove")`,
  `@patch("os.path.exists", ...)`, `mock_open`).
- **Construct the unit under test in a pytest fixture** (e.g. the `file_io` fixture) so each test
  starts from a clean, identically-configured object.
- **Never construct a real tkinter object.** The `display` fixture neutralizes `Tk.__init__`,
  mocks the inherited Tk methods the constructor calls, and replaces every widget class with a
  `_distinct_widget` side effect so each widget attribute is its own assertable mock. It returns a
  `SimpleNamespace` bundling the display and its mocks, and can be parametrized indirectly to
  supply persisted settings:
  `@pytest.mark.parametrize("display", [{"theme": "Light"}], indirect=True)`.
- **Name unasserted mock parameters with a leading underscore** (`_mock_os_exists`) and reserve
  plain names (`mock_os_remove`) for mocks you assert against.

## Follow the FIRST principles

- **Fast** — No real file, PDF, or GUI I/O; mock it. The whole `pytest tests/` run stays quick.
- **Independent** — No ordering dependencies or shared mutable state between tests. Each test
  builds its own object via a fixture and asserts on its own data.
- **Repeatable** — Deterministic on every run and machine. Do not rely on the real filesystem, the
  clock, or the `automated-invoice-testing` submodule — that submodule drives the *integration*
  test, not unit tests.
- **Self-validating** — Each test asserts a clear pass/fail (`assert ... ==`,
  `assert_called_once_with(...)`). Never require manual inspection of `logs/` output.
- **Timely** — Add or extend tests alongside any new branch or utility function, in the same
  change.

## Conventions

Give each test a docstring describing what it verifies, with an `Args:` block documenting each
mock/fixture parameter, and group tests for a given function under the `###`-bordered comment
banners used throughout `tests/`:

```python
###############################################################################
###                  InvoiceAppDisplay -> handle_about()                    ###
###############################################################################
```

**Import the names under test explicitly — never `from <module> import *`.** A wildcard
import binds whatever the module happens to export, so a name deleted or renamed in `source/`
fails at the point of *use*, in one test, rather than at import, in every test that file holds —
which makes a rename far harder to trace. Import lists are sorted and parenthesized across lines
once they no longer fit on one.

**Keep the parenthesized type in these `Args:` entries** — `display (pytest.fixture)`,
`mock_show_popup (unittest.mock.MagicMock)`. Test parameters are unannotated, so unlike in
`source/` the docstring is the only place the type is written.

**One fixture convention: build the unit under test in a pytest fixture**, and give a test that
needs a differently-constructed object its arguments through indirect parametrization
(`@pytest.mark.parametrize("window", [{"return_value": "copied"}], indirect=True)`) rather than a
`_build_window(...)`-style helper. The helper form left this repo with the shared subwindow
classes; do not reintroduce it. A fixture that patches widget classes `yield`s from **inside** its
`with` block, so the patches stay live for the test body and the patched classes themselves can be
asserted against — see `button_cls` in `tests/test_InvoiceDiscoveryWindow.py`.

**Do not add tests here for anything owned by `fishbowl-common`.** Its classes and windows
(`ThemedSubwindow`, `MessageWindow`, `AboutWindow`, `FileEditorWindow`, `UpdateWindow`,
`PatchNotesWindow`, `Tooltip`, `UpdateCoordinator`, `SettingsRepository`, `PatchNotes`) are
tested upstream and deliberately have **no counterpart here**. This repo tests its own classes and
the wiring around the shared ones — that the coordinator was constructed with the right arguments,
that a callback is forwarded — never the shared behavior itself.
