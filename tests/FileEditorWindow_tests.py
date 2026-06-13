import tkinter as tk
import pytest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from source.FileEditorWindow import FileEditorWindow
from source.color_theme import DARK
from source.font_settings import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE


###############################################################################
###                    FileEditorWindow -> Test Helpers                     ###
###############################################################################
def _distinct_widget(*_args, **_kwargs):
    """
    Side effect for patched tkinter widget classes that returns a fresh
    MagicMock for every constructed widget, so each widget attribute on the
    window (e.g. text_box vs. save_button) is a distinct mock that can be
    asserted on independently.
    """

    return MagicMock()


def _build_window(editable: bool, save_callback=None, initial_text: str = "file body"):
    """
    Builds a FileEditorWindow in complete isolation from tkinter: the real
    Toplevel.__init__ is neutralized, the inherited methods the constructor calls
    (title/configure) are mocked, and every widget class is replaced so no real
    window or widgets are created.

    Args:
        editable (bool): Whether to build the window in editable or read-only mode
        save_callback (callable | None): The save callback to pass through
        initial_text (str): The initial text the window displays

    Returns:
        types.SimpleNamespace: Holds the constructed window (`window`) and the
            file path it was bound to (`file_path`).
    """

    file_path = Path("Configs/Sales_Reps.txt")

    with (
        patch.object(tk.Toplevel, "__init__", return_value=None),
        patch.object(FileEditorWindow, "title"),
        patch.object(FileEditorWindow, "configure"),
        patch("source.FileEditorWindow.tk.Frame", side_effect=_distinct_widget),
        patch("source.FileEditorWindow.tk.Button", side_effect=_distinct_widget),
        patch(
            "source.FileEditorWindow.scrolledtext.ScrolledText",
            side_effect=_distinct_widget,
        ),
    ):

        window = FileEditorWindow(
            parent=MagicMock(),
            title="Sales Reps",
            file_path=file_path,
            initial_text=initial_text,
            theme=DARK,
            font_family=DEFAULT_FONT_FAMILY,
            font_size=DEFAULT_FONT_SIZE,
            editable=editable,
            save_callback=save_callback,
        )

    return SimpleNamespace(window=window, file_path=file_path)


###############################################################################
###                Tests FileEditorWindow -> build_widgets()                ###
###############################################################################
def test_editable_window_inserts_text_and_builds_buttons():
    """
    Verifies that an editable window inserts the initial text into the text box,
    leaves it editable, and creates both a Save button and a Close button placed
    next to it.
    """

    built = _build_window(editable=True, save_callback=MagicMock())

    # The current file contents are shown in the text box
    built.window.text_box.insert.assert_called_once_with(tk.END, "file body")

    # The text box is not disabled and both buttons exist
    built.window.text_box.configure.assert_not_called()
    assert built.window.save_button is not None
    assert built.window.close_button is not None

    # Save sits in the first column, Close next to it in the second
    built.window.save_button.grid.assert_called_once_with(row=0, column=0, padx=10)
    built.window.close_button.grid.assert_called_once_with(row=0, column=1, padx=10)


def test_readonly_window_disables_text_and_has_only_close_button():
    """
    Verifies that a read-only window inserts the initial text, disables editing on
    the text box, creates no Save button, and places the Close button where the
    Save button would have been.
    """

    built = _build_window(editable=False)

    # The contents are shown, then the text box is disabled to prevent editing
    built.window.text_box.insert.assert_called_once_with(tk.END, "file body")
    built.window.text_box.configure.assert_called_once_with(state="disabled")

    # No Save button is created, and Close takes the first column (Save's spot)
    assert built.window.save_button is None
    assert built.window.close_button is not None
    built.window.close_button.grid.assert_called_once_with(row=0, column=0, padx=10)


def test_close_button_is_wired_to_destroy():
    """
    Verifies that the Close button's command is the window's destroy method, so
    pressing it dismisses the window.
    """

    with (
        patch.object(tk.Toplevel, "__init__", return_value=None),
        patch.object(FileEditorWindow, "title"),
        patch.object(FileEditorWindow, "configure"),
        patch("source.FileEditorWindow.tk.Frame", side_effect=_distinct_widget),
        patch("source.FileEditorWindow.tk.Button", side_effect=_distinct_widget) as mock_button,
        patch(
            "source.FileEditorWindow.scrolledtext.ScrolledText",
            side_effect=_distinct_widget,
        ),
    ):

        window = FileEditorWindow(
            parent=MagicMock(),
            title="Results Log",
            file_path=Path("logs/results.txt"),
            initial_text="log body",
            theme=DARK,
            font_family=DEFAULT_FONT_FAMILY,
            font_size=DEFAULT_FONT_SIZE,
            editable=False,
        )

        # Find the Close button's construction call and confirm its command is destroy
        close_call = next(
            c for c in mock_button.call_args_list if c.kwargs.get("text") == "Close"
        )
        assert close_call.kwargs["command"] == window.destroy


###############################################################################
###                 Tests FileEditorWindow -> handle_save()                 ###
###############################################################################
def test_handle_save_forwards_path_and_stripped_contents():
    """
    Verifies that handle_save reads the text box contents, strips the trailing
    newline tkinter appends, and forwards the bound file path and contents to the
    save callback.
    """

    save_callback = MagicMock()
    built = _build_window(editable=True, save_callback=save_callback)

    # tkinter's Text.get returns the contents with a trailing newline appended
    built.window.text_box.get.return_value = "edited contents\n"

    built.window.handle_save()

    # The text box is read from the start to the end
    built.window.text_box.get.assert_called_once_with("1.0", tk.END)

    # The bound file path and trailing-newline-stripped contents are forwarded
    save_callback.assert_called_once_with(built.file_path, "edited contents")


def test_handle_save_without_callback_does_nothing():
    """
    Verifies that handle_save does not raise when no save callback was provided.
    """

    built = _build_window(editable=True, save_callback=None)
    built.window.text_box.get.return_value = "contents\n"

    # No callback is wired, so saving is a no-op rather than an error
    built.window.handle_save()
