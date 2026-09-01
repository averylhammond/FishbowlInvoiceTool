import tkinter as tk
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fishbowl_common.gui import DARK, DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE

from source.gui.InvoiceDiscoveryWindow import InvoiceDiscoveryWindow


###############################################################################
###                  InvoiceDiscoveryWindow -> Test Helpers                 ###
###############################################################################
def _distinct_widget(*_args, **_kwargs):
    """
    Side effect for patched tkinter widget classes that returns a fresh
    MagicMock for every constructed widget, so each widget attribute on the
    window (e.g. browse_button vs. status_box) is a distinct mock that can be
    asserted on independently.
    """

    return MagicMock()


###############################################################################
###                  InvoiceDiscoveryWindow -> Test Fixture                 ###
###############################################################################
@pytest.fixture
def window(request):
    """
    Builds an InvoiceDiscoveryWindow in complete isolation from tkinter: the real
    Toplevel.__init__ is neutralized, the inherited methods the constructor calls
    (title/configure) are mocked, and every widget class is replaced so no real
    window or widgets are created. The patches stay active for the duration of
    each test, so the widget classes can also be asserted against from the test
    body.

    The copy callback's behavior can be customized per test by parametrizing the
    fixture indirectly with the keyword arguments to build its mock from (e.g.
    @pytest.mark.parametrize("window", [{"return_value": "copied"}],
    indirect=True)); when not parametrized, the callback is a bare MagicMock.

    Returns:
        types.SimpleNamespace: Holds the constructed window (`window`), the copy
            callback it was built with (`copy_callback`), and the patched
            tk.Button class (`button_cls`).
    """

    # Copy-callback behavior supplied indirectly by a test, or a bare mock when not
    copy_callback = MagicMock(**getattr(request, "param", {}))

    with (
        patch.object(tk.Toplevel, "__init__", return_value=None),
        patch.object(InvoiceDiscoveryWindow, "title"),
        patch.object(InvoiceDiscoveryWindow, "configure"),
        patch.object(InvoiceDiscoveryWindow, "_center_over_parent"),
        patch("source.gui.InvoiceDiscoveryWindow.tk.StringVar", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Label", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Frame", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Entry", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Button", side_effect=_distinct_widget) as mock_button,
        patch(
            "source.gui.InvoiceDiscoveryWindow.scrolledtext.ScrolledText",
            side_effect=_distinct_widget,
        ),
        patch("source.gui.InvoiceDiscoveryWindow.Tooltip", side_effect=_distinct_widget),
    ):
        built_window = InvoiceDiscoveryWindow(
            parent=MagicMock(),
            title="Discover Invoices",
            theme=DARK,
            font_family=DEFAULT_FONT_FAMILY,
            font_size=DEFAULT_FONT_SIZE,
            copy_callback=copy_callback,
        )

        yield SimpleNamespace(
            window=built_window,
            copy_callback=copy_callback,
            button_cls=mock_button,
        )


###############################################################################
###             Tests InvoiceDiscoveryWindow -> build_widgets()             ###
###############################################################################
def test_build_widgets_creates_widgets_and_disables_status_box(window):
    """
    Verifies that build_widgets constructs the action buttons and the status box,
    and that the status box starts disabled (read-only).

    Args:
        window (pytest.fixture): Provides the window and its mocks
    """

    # The action buttons and status area are created
    assert window.window.browse_button is not None
    assert window.window.copy_button is not None
    assert window.window.close_button is not None
    assert window.window.status_box is not None

    # The status box is read-only until a status line is written
    window.window.status_box.configure.assert_called_once_with(state="disabled")


def test_close_button_is_wired_to_destroy(window):
    """
    Verifies that the Close button's command is the window's destroy method, so
    pressing it dismisses the window.

    Args:
        window (pytest.fixture): Provides the window and its mocks
    """

    # Find the Close button's construction call and confirm its command is destroy
    close_call = next(c for c in window.button_cls.call_args_list if c.kwargs.get("text") == "Close")
    assert close_call.kwargs["command"] == window.window.destroy


###############################################################################
###               Tests InvoiceDiscoveryWindow -> handle_browse()           ###
###############################################################################
@patch.object(InvoiceDiscoveryWindow, "_default_browse_dir", return_value="/downloads")
@patch("source.gui.InvoiceDiscoveryWindow.filedialog.askopenfilenames")
def test_handle_browse_adds_selected_files(mock_ask, _mock_default_dir, window):
    """
    Verifies that handle_browse appends the user's selected PDFs to the pending
    list and updates the selection display with their names.

    Args:
        mock_ask (unittest.mock.MagicMock): Mocks filedialog.askopenfilenames
        _mock_default_dir (unittest.mock.MagicMock): Mocks the default browse dir
        window (pytest.fixture): Provides the window and its mocks
    """

    # The user selects two invoices
    mock_ask.return_value = ("/downloads/a.pdf", "/downloads/b.pdf")

    window.window.handle_browse()

    # Both files are queued and the selection display lists their names
    assert window.window.pending_files == [
        Path("/downloads/a.pdf"),
        Path("/downloads/b.pdf"),
    ]
    window.window.selection_var.set.assert_called_once_with("a.pdf, b.pdf")


@patch.object(InvoiceDiscoveryWindow, "_default_browse_dir", return_value="/downloads")
@patch("source.gui.InvoiceDiscoveryWindow.filedialog.askopenfilenames")
def test_handle_browse_cancel_leaves_selection_untouched(mock_ask, _mock_default_dir, window):
    """
    Verifies that cancelling the file dialog (empty selection) does not change the
    pending list or update the selection display.

    Args:
        mock_ask (unittest.mock.MagicMock): Mocks filedialog.askopenfilenames
        _mock_default_dir (unittest.mock.MagicMock): Mocks the default browse dir
        window (pytest.fixture): Provides the window and its mocks
    """

    # The user cancels the dialog
    mock_ask.return_value = ()

    window.window.handle_browse()

    # Nothing is queued and the selection display is not updated
    assert window.window.pending_files == []
    window.window.selection_var.set.assert_not_called()


###############################################################################
###                Tests InvoiceDiscoveryWindow -> handle_copy()            ###
###############################################################################
@pytest.mark.parametrize("window", [{"return_value": "copied"}], indirect=True)
def test_handle_copy_copies_each_pending_file(window):
    """
    Verifies that handle_copy copies each pending file (without overwriting) and
    clears the pending selection afterwards.

    Args:
        window (pytest.fixture): Provides the window and a copy callback that
            reports every copy as successful
    """

    window.window.pending_files = [Path("a.pdf"), Path("b.pdf")]

    window.window.handle_copy()

    # Each file is copied without overwriting, and the selection is cleared
    window.copy_callback.assert_any_call(Path("a.pdf"), False)
    window.copy_callback.assert_any_call(Path("b.pdf"), False)
    assert window.window.pending_files == []
    window.window.selection_var.set.assert_called_with("")


def test_handle_copy_no_files_reports_and_does_not_copy(window):
    """
    Verifies that handle_copy does nothing but report a status message when no
    files have been selected.

    Args:
        window (pytest.fixture): Provides the window and its mocks
    """

    window.window.pending_files = []

    window.window.handle_copy()

    # No copy is attempted when there is nothing selected
    window.copy_callback.assert_not_called()


@pytest.mark.parametrize("window", [{"return_value": "error"}], indirect=True)
def test_handle_copy_reports_copy_failure(window):
    """
    Verifies that handle_copy reports a failure status (without raising) when the
    copy callback returns "error", and still clears the pending selection.

    Args:
        window (pytest.fixture): Provides the window and a copy callback that
            reports the copy as failed
    """

    window.window.pending_files = [Path("a.pdf")]

    window.window.handle_copy()

    # The failed file is still attempted and the selection is cleared afterwards
    window.copy_callback.assert_called_once_with(Path("a.pdf"), False)
    assert window.window.pending_files == []


@patch("source.gui.InvoiceDiscoveryWindow.messagebox.askyesno", return_value=True)
@pytest.mark.parametrize("window", [{"side_effect": ["exists", "copied"]}], indirect=True)
def test_handle_copy_overwrites_when_confirmed(mock_askyesno, window):
    """
    Verifies that when a file already exists and the user confirms, handle_copy
    re-issues the copy with overwrite=True.

    Args:
        mock_askyesno (unittest.mock.MagicMock): Mocks the overwrite confirmation
        window (pytest.fixture): Provides the window and a copy callback that
            first reports the file exists, then reports the retry as successful
    """

    window.window.pending_files = [Path("a.pdf")]

    window.window.handle_copy()

    # The user is asked to confirm, then the copy is retried with overwrite=True
    mock_askyesno.assert_called_once()
    window.copy_callback.assert_any_call(Path("a.pdf"), False)
    window.copy_callback.assert_any_call(Path("a.pdf"), True)


@patch("source.gui.InvoiceDiscoveryWindow.messagebox.askyesno", return_value=False)
@pytest.mark.parametrize("window", [{"return_value": "exists"}], indirect=True)
def test_handle_copy_skips_when_overwrite_declined(mock_askyesno, window):
    """
    Verifies that when a file already exists and the user declines, handle_copy
    skips the file and does not re-issue the copy.

    Args:
        mock_askyesno (unittest.mock.MagicMock): Mocks the overwrite confirmation
        window (pytest.fixture): Provides the window and a copy callback that
            reports the file already exists
    """

    window.window.pending_files = [Path("a.pdf")]

    window.window.handle_copy()

    # The file is checked once (overwrite=False) and never overwritten
    mock_askyesno.assert_called_once()
    window.copy_callback.assert_called_once_with(Path("a.pdf"), False)


###############################################################################
###            Tests InvoiceDiscoveryWindow -> _default_browse_dir()        ###
###############################################################################
@patch("source.gui.InvoiceDiscoveryWindow.Path")
def test_default_browse_dir_prefers_downloads(mock_path, window):
    """
    Verifies that _default_browse_dir returns the Downloads folder when it exists.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        window (pytest.fixture): Provides the window and its mocks
    """

    # Downloads exists, so it is preferred as the starting directory
    downloads = mock_path.home.return_value.__truediv__.return_value
    downloads.exists.return_value = True

    assert window.window._default_browse_dir() == str(downloads)


@patch("source.gui.InvoiceDiscoveryWindow.Path")
def test_default_browse_dir_falls_back_to_home(mock_path, window):
    """
    Verifies that _default_browse_dir falls back to the home folder when the
    Downloads folder does not exist.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        window (pytest.fixture): Provides the window and its mocks
    """

    # Downloads does not exist, so the home folder is used instead
    downloads = mock_path.home.return_value.__truediv__.return_value
    downloads.exists.return_value = False

    assert window.window._default_browse_dir() == str(mock_path.home.return_value)
