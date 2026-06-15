import tkinter as tk
import pytest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from source.gui.InvoiceDiscoveryWindow import InvoiceDiscoveryWindow
from source.gui.color_theme import DARK
from source.gui.font_settings import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE


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


def _build_window(copy_callback=None):
    """
    Builds an InvoiceDiscoveryWindow in complete isolation from tkinter: the real
    Toplevel.__init__ is neutralized, the inherited methods the constructor calls
    (title/configure) are mocked, and every widget class is replaced so no real
    window or widgets are created.

    Args:
        copy_callback (callable | None): The copy callback to pass through;
            defaults to a fresh MagicMock when not supplied

    Returns:
        types.SimpleNamespace: Holds the constructed window (`window`) and the
            copy callback it was built with (`copy_callback`).
    """

    if copy_callback is None:
        copy_callback = MagicMock()

    with (
        patch.object(tk.Toplevel, "__init__", return_value=None),
        patch.object(InvoiceDiscoveryWindow, "title"),
        patch.object(InvoiceDiscoveryWindow, "configure"),
        patch(
            "source.gui.InvoiceDiscoveryWindow.tk.StringVar", side_effect=_distinct_widget
        ),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Label", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Frame", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Entry", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Button", side_effect=_distinct_widget),
        patch(
            "source.gui.InvoiceDiscoveryWindow.scrolledtext.ScrolledText",
            side_effect=_distinct_widget,
        ),
        patch("source.gui.InvoiceDiscoveryWindow.Tooltip", side_effect=_distinct_widget),
    ):

        window = InvoiceDiscoveryWindow(
            parent=MagicMock(),
            title="Discover Invoices",
            theme=DARK,
            font_family=DEFAULT_FONT_FAMILY,
            font_size=DEFAULT_FONT_SIZE,
            copy_callback=copy_callback,
        )

    return SimpleNamespace(window=window, copy_callback=copy_callback)


###############################################################################
###             Tests InvoiceDiscoveryWindow -> build_widgets()             ###
###############################################################################
def test_build_widgets_creates_widgets_and_disables_status_box():
    """
    Verifies that build_widgets constructs the action buttons and the status box,
    and that the status box starts disabled (read-only).
    """

    built = _build_window()

    # The action buttons and status area are created
    assert built.window.browse_button is not None
    assert built.window.copy_button is not None
    assert built.window.close_button is not None
    assert built.window.status_box is not None

    # The status box is read-only until a status line is written
    built.window.status_box.configure.assert_called_once_with(state="disabled")


def test_close_button_is_wired_to_destroy():
    """
    Verifies that the Close button's command is the window's destroy method, so
    pressing it dismisses the window.
    """

    with (
        patch.object(tk.Toplevel, "__init__", return_value=None),
        patch.object(InvoiceDiscoveryWindow, "title"),
        patch.object(InvoiceDiscoveryWindow, "configure"),
        patch(
            "source.gui.InvoiceDiscoveryWindow.tk.StringVar", side_effect=_distinct_widget
        ),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Label", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Frame", side_effect=_distinct_widget),
        patch("source.gui.InvoiceDiscoveryWindow.tk.Entry", side_effect=_distinct_widget),
        patch(
            "source.gui.InvoiceDiscoveryWindow.tk.Button", side_effect=_distinct_widget
        ) as mock_button,
        patch(
            "source.gui.InvoiceDiscoveryWindow.scrolledtext.ScrolledText",
            side_effect=_distinct_widget,
        ),
        patch("source.gui.InvoiceDiscoveryWindow.Tooltip", side_effect=_distinct_widget),
    ):

        window = InvoiceDiscoveryWindow(
            parent=MagicMock(),
            title="Discover Invoices",
            theme=DARK,
            font_family=DEFAULT_FONT_FAMILY,
            font_size=DEFAULT_FONT_SIZE,
            copy_callback=MagicMock(),
        )

        # Find the Close button's construction call and confirm its command is destroy
        close_call = next(
            c for c in mock_button.call_args_list if c.kwargs.get("text") == "Close"
        )
        assert close_call.kwargs["command"] == window.destroy


###############################################################################
###               Tests InvoiceDiscoveryWindow -> handle_browse()           ###
###############################################################################
@patch.object(InvoiceDiscoveryWindow, "_default_browse_dir", return_value="/downloads")
@patch("source.gui.InvoiceDiscoveryWindow.filedialog.askopenfilenames")
def test_handle_browse_adds_selected_files(mock_ask, _mock_default_dir):
    """
    Verifies that handle_browse appends the user's selected PDFs to the pending
    list and updates the selection display with their names.

    Args:
        mock_ask (unittest.mock.MagicMock): Mocks filedialog.askopenfilenames
        _mock_default_dir (unittest.mock.MagicMock): Mocks the default browse dir
    """

    built = _build_window()

    # The user selects two invoices
    mock_ask.return_value = ("/downloads/a.pdf", "/downloads/b.pdf")

    built.window.handle_browse()

    # Both files are queued and the selection display lists their names
    assert built.window.pending_files == [
        Path("/downloads/a.pdf"),
        Path("/downloads/b.pdf"),
    ]
    built.window.selection_var.set.assert_called_once_with("a.pdf, b.pdf")


@patch.object(InvoiceDiscoveryWindow, "_default_browse_dir", return_value="/downloads")
@patch("source.gui.InvoiceDiscoveryWindow.filedialog.askopenfilenames")
def test_handle_browse_cancel_leaves_selection_untouched(mock_ask, _mock_default_dir):
    """
    Verifies that cancelling the file dialog (empty selection) does not change the
    pending list or update the selection display.

    Args:
        mock_ask (unittest.mock.MagicMock): Mocks filedialog.askopenfilenames
        _mock_default_dir (unittest.mock.MagicMock): Mocks the default browse dir
    """

    built = _build_window()

    # The user cancels the dialog
    mock_ask.return_value = ()

    built.window.handle_browse()

    # Nothing is queued and the selection display is not updated
    assert built.window.pending_files == []
    built.window.selection_var.set.assert_not_called()


###############################################################################
###                Tests InvoiceDiscoveryWindow -> handle_copy()            ###
###############################################################################
def test_handle_copy_copies_each_pending_file():
    """
    Verifies that handle_copy copies each pending file (without overwriting) and
    clears the pending selection afterwards.
    """

    copy_callback = MagicMock(return_value="copied")
    built = _build_window(copy_callback=copy_callback)
    built.window.pending_files = [Path("a.pdf"), Path("b.pdf")]

    built.window.handle_copy()

    # Each file is copied without overwriting, and the selection is cleared
    copy_callback.assert_any_call(Path("a.pdf"), False)
    copy_callback.assert_any_call(Path("b.pdf"), False)
    assert built.window.pending_files == []
    built.window.selection_var.set.assert_called_with("")


def test_handle_copy_no_files_reports_and_does_not_copy():
    """
    Verifies that handle_copy does nothing but report a status message when no
    files have been selected.
    """

    copy_callback = MagicMock()
    built = _build_window(copy_callback=copy_callback)
    built.window.pending_files = []

    built.window.handle_copy()

    # No copy is attempted when there is nothing selected
    copy_callback.assert_not_called()


def test_handle_copy_reports_copy_failure():
    """
    Verifies that handle_copy reports a failure status (without raising) when the
    copy callback returns "error", and still clears the pending selection.
    """

    copy_callback = MagicMock(return_value="error")
    built = _build_window(copy_callback=copy_callback)
    built.window.pending_files = [Path("a.pdf")]

    built.window.handle_copy()

    # The failed file is still attempted and the selection is cleared afterwards
    copy_callback.assert_called_once_with(Path("a.pdf"), False)
    assert built.window.pending_files == []


@patch("source.gui.InvoiceDiscoveryWindow.messagebox.askyesno", return_value=True)
def test_handle_copy_overwrites_when_confirmed(mock_askyesno):
    """
    Verifies that when a file already exists and the user confirms, handle_copy
    re-issues the copy with overwrite=True.

    Args:
        mock_askyesno (unittest.mock.MagicMock): Mocks the overwrite confirmation
    """

    # First call reports the file exists; the confirmed overwrite then succeeds
    copy_callback = MagicMock(side_effect=["exists", "copied"])
    built = _build_window(copy_callback=copy_callback)
    built.window.pending_files = [Path("a.pdf")]

    built.window.handle_copy()

    # The user is asked to confirm, then the copy is retried with overwrite=True
    mock_askyesno.assert_called_once()
    copy_callback.assert_any_call(Path("a.pdf"), False)
    copy_callback.assert_any_call(Path("a.pdf"), True)


@patch("source.gui.InvoiceDiscoveryWindow.messagebox.askyesno", return_value=False)
def test_handle_copy_skips_when_overwrite_declined(mock_askyesno):
    """
    Verifies that when a file already exists and the user declines, handle_copy
    skips the file and does not re-issue the copy.

    Args:
        mock_askyesno (unittest.mock.MagicMock): Mocks the overwrite confirmation
    """

    copy_callback = MagicMock(return_value="exists")
    built = _build_window(copy_callback=copy_callback)
    built.window.pending_files = [Path("a.pdf")]

    built.window.handle_copy()

    # The file is checked once (overwrite=False) and never overwritten
    mock_askyesno.assert_called_once()
    copy_callback.assert_called_once_with(Path("a.pdf"), False)


###############################################################################
###            Tests InvoiceDiscoveryWindow -> _default_browse_dir()        ###
###############################################################################
@patch("source.gui.InvoiceDiscoveryWindow.Path")
def test_default_browse_dir_prefers_downloads(mock_path):
    """
    Verifies that _default_browse_dir returns the Downloads folder when it exists.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
    """

    built = _build_window()

    # Downloads exists, so it is preferred as the starting directory
    downloads = mock_path.home.return_value.__truediv__.return_value
    downloads.exists.return_value = True

    assert built.window._default_browse_dir() == str(downloads)


@patch("source.gui.InvoiceDiscoveryWindow.Path")
def test_default_browse_dir_falls_back_to_home(mock_path):
    """
    Verifies that _default_browse_dir falls back to the home folder when the
    Downloads folder does not exist.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
    """

    built = _build_window()

    # Downloads does not exist, so the home folder is used instead
    downloads = mock_path.home.return_value.__truediv__.return_value
    downloads.exists.return_value = False

    assert built.window._default_browse_dir() == str(mock_path.home.return_value)
