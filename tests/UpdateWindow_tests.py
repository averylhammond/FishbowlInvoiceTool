import tkinter as tk
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from source.gui.UpdateWindow import UpdateWindow
from source.gui.color_theme import DARK
from source.gui.font_settings import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE


###############################################################################
###                      UpdateWindow -> Test Helpers                      ###
###############################################################################
def _distinct_widget(*_args, **_kwargs):
    """
    Side effect for patched tkinter widget classes that returns a fresh
    MagicMock for every constructed widget, so each widget attribute on the
    window (e.g. info_label vs. download_button vs. close_button) is a distinct
    mock that can be asserted on independently.
    """

    return MagicMock()


def _build_window(latest_version="9.9.9", release_url="https://example.com/release"):
    """
    Builds an UpdateWindow in complete isolation from tkinter: the real
    Toplevel.__init__ is neutralized, the inherited methods the constructor calls
    (title/configure) are mocked, and every widget class is replaced so no real
    window or widgets are created.

    Args:
        latest_version (str): The available version to build the window with
        release_url (str): The release URL to build the window with

    Returns:
        types.SimpleNamespace: Holds the constructed window (`window`) and the
            patched tk.Label/tk.Button classes (`label_cls`, `button_cls`) so
            tests can assert on how each widget was constructed.
    """

    with (
        patch.object(tk.Toplevel, "__init__", return_value=None),
        patch.object(UpdateWindow, "title"),
        patch.object(UpdateWindow, "configure"),
        patch.object(UpdateWindow, "_center_over_parent"),
        patch(
            "source.gui.UpdateWindow.tk.Label", side_effect=_distinct_widget
        ) as label_cls,
        patch(
            "source.gui.UpdateWindow.tk.Button", side_effect=_distinct_widget
        ) as button_cls,
    ):

        window = UpdateWindow(
            parent=MagicMock(),
            title="Update Available",
            latest_version=latest_version,
            release_url=release_url,
            theme=DARK,
            font_family=DEFAULT_FONT_FAMILY,
            font_size=DEFAULT_FONT_SIZE,
        )

    return SimpleNamespace(window=window, label_cls=label_cls, button_cls=button_cls)


###############################################################################
###                 Tests UpdateWindow -> build_widgets()                  ###
###############################################################################
def test_build_widgets_creates_label_and_buttons():
    """
    Verifies that build_widgets constructs the info label, the Download button,
    and the Close button, storing each on the window.
    """

    built = _build_window()

    assert built.window.info_label is not None
    assert built.window.download_button is not None
    assert built.window.close_button is not None


def test_info_label_shows_available_version():
    """
    Verifies that the info label announces the available version that was passed
    in, so the user sees which newer version is available.
    """

    built = _build_window(latest_version="9.9.9")

    label_call = built.label_cls.call_args
    assert label_call.kwargs["text"] == "Version 9.9.9 is available"


def test_label_and_buttons_use_theme_and_font():
    """
    Verifies that the label and both buttons are styled with the snapshotted theme
    colors and font, matching the rest of the application.
    """

    built = _build_window()

    # The label uses the theme background, label foreground, and bold font
    label_kwargs = built.label_cls.call_args.kwargs
    assert label_kwargs["bg"] == DARK.bg_main
    assert label_kwargs["fg"] == DARK.label_fg
    assert label_kwargs["font"] == (DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE, "bold")

    # Both buttons use the theme button colors and bold font
    for button_call in built.button_cls.call_args_list:
        assert button_call.kwargs["bg"] == DARK.button_bg
        assert button_call.kwargs["fg"] == DARK.button_fg
        assert button_call.kwargs["font"] == (
            DEFAULT_FONT_FAMILY,
            DEFAULT_FONT_SIZE,
            "bold",
        )


def test_close_button_is_wired_to_destroy():
    """
    Verifies that the Close button's command is the window's destroy method, so
    pressing it dismisses the window.
    """

    built = _build_window()

    # The Close button is the second button constructed (after Download)
    close_kwargs = built.button_cls.call_args_list[1].kwargs
    assert close_kwargs["text"] == "Close"
    assert close_kwargs["command"] == built.window.destroy


def test_download_button_is_wired_to_open_release_page():
    """
    Verifies that the Download button's command opens the release page, so
    pressing it sends the user to the release on GitHub.
    """

    built = _build_window()

    # The Download button is the first button constructed
    download_kwargs = built.button_cls.call_args_list[0].kwargs
    assert download_kwargs["text"] == "Download"
    assert download_kwargs["command"] == built.window._open_release_page


###############################################################################
###               Tests UpdateWindow -> _open_release_page()               ###
###############################################################################
def test_open_release_page_opens_url_in_browser():
    """
    Verifies that _open_release_page opens the release URL in the user's browser.
    """

    built = _build_window(release_url="https://example.com/release")

    with patch("source.gui.UpdateWindow.webbrowser.open") as mock_open:
        built.window._open_release_page()

    mock_open.assert_called_once_with("https://example.com/release")
