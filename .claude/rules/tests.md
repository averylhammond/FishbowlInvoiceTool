---
paths:
  - "tests/**"
---

# Unit testing conventions

Unit tests live in `tests/`, one `tests/<ModuleName>_tests.py` per module under `source/`.
`tests/__init__.py` is empty but load-bearing: with it present, pytest's prepend import mode puts
the repo root on `sys.path`, which is what makes `from source... import` resolve. There is no
`conftest.py`; coverage configuration lives in `.coveragerc`, which measures `./source` and omits
`main.py`, `tests/`, the venvs, `source/__init__.py` and `source/constants.py`.

`tests/InvoiceProcessor_tests.py` (a class with injected collaborators) and
`tests/InvoiceAppDisplay_tests.py` (the widget-patching fixture) are the two reference
implementations — mirror them rather than inventing new patterns.

## Test one object in isolation

Every unit test exercises exactly **one** class or function. Replace **all** collaborating
objects with mocks so a failure points unambiguously at the unit being tested — never let a unit
test depend on the real behavior of another class, the filesystem, a PDF, or the GUI.

- **Mock injected collaborators with `MagicMock(spec=Collaborator)`** and pass them into the
  constructor. See the `mock_file_io` and `invoice_processor` fixtures in
  `tests/InvoiceProcessor_tests.py`, where `InvoiceProcessor` is built with a
  `MagicMock(spec=InvoiceAppFileIO)` so no real file I/O occurs. The `spec=` argument keeps the
  mock honest — it only allows attributes and methods the real class defines.
- **Mock module-level dependencies with `@patch` / `mock_open`.** For classes that call `os`,
  `open`, or pypdf directly, patch those calls instead of touching the real filesystem — see
  `tests/InvoiceAppFileIO_tests.py` (e.g. `@patch("os.remove")`,
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

- **Fast** — No real file, PDF, or GUI I/O; mock it. The whole `pytest tests/*` run stays quick.
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

**Do not add tests here for anything owned by `fishbowl-common`.** Its classes and windows
(`ThemedSubwindow`, `MessageWindow`, `AboutWindow`, `FileEditorWindow`, `UpdateWindow`,
`PatchNotesWindow`, `Tooltip`, `UpdateCoordinator`, `SettingsRepository`, `PatchNotes`) are
tested upstream and deliberately have **no counterpart here**. This repo tests its own classes and
the wiring around the shared ones — that the coordinator was constructed with the right arguments,
that a callback is forwarded — never the shared behavior itself.
