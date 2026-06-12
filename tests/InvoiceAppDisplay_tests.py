import tkinter as tk
import pytest
from types import SimpleNamespace
from unittest.mock import patch, call, MagicMock

from source.Invoice import Invoice
from source.InvoiceAppDisplay import InvoiceAppDisplay
from source.color_theme import DARK, LIGHT
from source.font_settings import DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE
from source.constants import (
    INVOICES_PATH,
    PAYMENT_TERMS_PATH,
    SALES_REPS_PATH,
    COST_CRITERIA_PATH,
    RESULTS_LOG_PATH,
    DEBUG_LOG_PATH,
)


###############################################################################
###                   InvoiceAppDisplay -> Test Helpers                     ###
###############################################################################
def _distinct_widget(*_args, **_kwargs):
    """
    Side effect for patched tkinter widget classes that returns a fresh
    MagicMock for every constructed widget, so each widget attribute on the
    display (e.g. title_label vs. output_box) is a distinct mock that can be
    asserted on independently.
    """

    return MagicMock()


###############################################################################
###                   InvoiceAppDisplay -> Test Fixture                     ###
###############################################################################
@pytest.fixture
def display():
    """
    Builds an InvoiceAppDisplay in complete isolation from tkinter: the real
    Tk.__init__ is neutralized, the inherited Tk methods the constructor calls
    (title/geometry/resizable/configure/config) are mocked, and every widget
    class is replaced so no real window or widgets are created. The patches stay
    active for the duration of each test so methods that reconfigure widgets
    (apply_theme/_apply_font) also run without a real display.

    Returns:
        types.SimpleNamespace: Holds the constructed display (`display`), the
            mocked Tk methods (`title`, `geometry`, `resizable`, `configure`,
            `config`), the mocked ArgumentProvider instance (`arg_provider`), and
            the process callback passed at construction (`process_callback`).
    """

    with (
        patch.object(tk.Tk, "__init__", return_value=None),
        patch.object(InvoiceAppDisplay, "title") as mock_title,
        patch.object(InvoiceAppDisplay, "geometry") as mock_geometry,
        patch.object(InvoiceAppDisplay, "resizable") as mock_resizable,
        patch.object(InvoiceAppDisplay, "configure") as mock_configure,
        patch.object(InvoiceAppDisplay, "config") as mock_config,
        patch("source.InvoiceAppDisplay.ArgumentProvider") as mock_arg_cls,
        patch("source.InvoiceAppDisplay.tk.StringVar"),
        patch("source.InvoiceAppDisplay.tk.Menu", side_effect=_distinct_widget),
        patch("source.InvoiceAppDisplay.tk.Label", side_effect=_distinct_widget),
        patch("source.InvoiceAppDisplay.tk.Frame", side_effect=_distinct_widget),
        patch("source.InvoiceAppDisplay.tk.Entry", side_effect=_distinct_widget),
        patch("source.InvoiceAppDisplay.tk.Button", side_effect=_distinct_widget),
        patch(
            "source.InvoiceAppDisplay.scrolledtext.ScrolledText",
            side_effect=_distinct_widget,
        ),
    ):

        # The callback the controller would normally supply; a mock is sufficient
        callback = MagicMock()

        built_display = InvoiceAppDisplay(
            process_callback=callback,
            title="Invoice Processor",
            window_resolution="750x750",
        )

        yield SimpleNamespace(
            display=built_display,
            title=mock_title,
            geometry=mock_geometry,
            resizable=mock_resizable,
            configure=mock_configure,
            config=mock_config,
            arg_provider=mock_arg_cls.return_value,
            process_callback=callback,
        )


###############################################################################
###                Tests InvoiceAppDisplay -> __init__()                    ###
###############################################################################
def test_init_sets_window_properties(display):
    """
    Verifies that __init__ applies the window title, resolution, and resizable
    settings using the values passed to the constructor.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    # Window chrome is configured from the constructor arguments
    display.title.assert_called_once_with("Invoice Processor")
    display.geometry.assert_called_once_with("750x750")
    display.resizable.assert_called_once_with(True, True)


def test_init_sets_default_state(display):
    """
    Verifies that __init__ initializes the default theme, font family, font size,
    process callback, and argument provider on the display.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    # The display starts on the default theme and font settings
    assert display.display.current_theme == DARK
    assert display.display.current_font_family == DEFAULT_FONT_FAMILY
    assert display.display.current_font_size == DEFAULT_FONT_SIZE

    # The process callback and argument provider are stored for later use
    assert display.display.process_callback is display.process_callback
    assert display.display.argument_provider is display.arg_provider


###############################################################################
###              Tests InvoiceAppDisplay -> build_widgets()                 ###
###############################################################################
def test_build_widgets_creates_all_widgets(display):
    """
    Verifies that build_widgets constructs every widget the display tracks,
    leaving none of the widget attributes at their initial None value.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    # Every widget attribute should have been assigned a constructed widget
    assert display.display.menu_bar is not None
    assert display.display.file_menu is not None
    assert display.display.edit_menu is not None
    assert display.display.view_menu is not None
    assert display.display.preferences_menu is not None
    assert display.display.title_label is not None
    assert display.display.file_frame is not None
    assert display.display.file_entry is not None
    assert display.display.browse_button is not None
    assert display.display.button_frame is not None
    assert display.display.process_invoice_button is not None
    assert display.display.exit_button is not None
    assert display.display.process_all_invoices_button is not None
    assert display.display.output_label is not None
    assert display.display.output_box is not None


def test_build_widgets_attaches_menu_bar(display):
    """
    Verifies that build_widgets registers the assembled menu bar on the window.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    # The menu bar is attached to the window exactly once
    display.config.assert_called_once_with(menu=display.display.menu_bar)


###############################################################################
###            Tests InvoiceAppDisplay -> handle_browse_button()            ###
###############################################################################
@patch("source.InvoiceAppDisplay.filedialog.askopenfilename")
def test_handle_browse_button_sets_selected_file(mock_askopenfilename, display):
    """
    Verifies that handle_browse_button stores the chosen file path on the
    selected_file variable when the user picks a file.

    Args:
        mock_askopenfilename (unittest.mock.MagicMock): Mocks the file dialog
        display (pytest.fixture): Provides the display and its mocks
    """

    # The user selects a PDF in the dialog
    mock_askopenfilename.return_value = "C:/invoices/order.pdf"

    display.display.handle_browse_button()

    # The chosen path is written to the selected_file variable
    display.display.selected_file.set.assert_called_once_with("C:/invoices/order.pdf")


@patch("source.InvoiceAppDisplay.filedialog.askopenfilename")
def test_handle_browse_button_no_selection(mock_askopenfilename, display):
    """
    Verifies that handle_browse_button leaves the selected_file variable
    untouched when the user cancels the dialog (empty path returned).

    Args:
        mock_askopenfilename (unittest.mock.MagicMock): Mocks the file dialog
        display (pytest.fixture): Provides the display and its mocks
    """

    # The user cancels the dialog, returning an empty string
    mock_askopenfilename.return_value = ""

    display.display.handle_browse_button()

    # No file path is stored when nothing is selected
    display.display.selected_file.set.assert_not_called()


###############################################################################
###           Tests InvoiceAppDisplay -> display_invoice_output()           ###
###############################################################################
def test_display_invoice_output_overwrites_by_default(display):
    """
    Verifies that display_invoice_output clears the output box and writes the
    invoice's formatted string when append_output is left at its default False.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.to_formatted_string.return_value = "formatted invoice"

    display.display.display_invoice_output(mock_invoice)

    # The box is cleared, then the formatted invoice is inserted
    display.display.output_box.delete.assert_called_once_with(1.0, tk.END)
    display.display.output_box.insert.assert_called_once_with(
        tk.END, "formatted invoice"
    )


def test_display_invoice_output_appends_when_requested(display):
    """
    Verifies that display_invoice_output appends a newline and the invoice's
    formatted string (without clearing) when append_output is True.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.to_formatted_string.return_value = "formatted invoice"

    display.display.display_invoice_output(mock_invoice, append_output=True)

    # A separating newline and the formatted invoice are inserted, nothing cleared
    display.display.output_box.delete.assert_not_called()
    display.display.output_box.insert.assert_has_calls(
        [call(tk.END, "\n"), call(tk.END, "formatted invoice")]
    )


def test_display_invoice_output_no_output_box(display):
    """
    Verifies that display_invoice_output safely does nothing when the output box
    has not been initialized.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    # Simulate the output box never having been built
    display.display.output_box = None
    mock_invoice = MagicMock(spec=Invoice)

    # No error should be raised, and the invoice is never formatted for display
    display.display.display_invoice_output(mock_invoice)
    mock_invoice.to_formatted_string.assert_not_called()


###############################################################################
###           Tests InvoiceAppDisplay -> handle_process_invoice()           ###
###############################################################################
@patch.object(InvoiceAppDisplay, "show_error_popup")
def test_handle_process_invoice_no_file_shows_error(mock_show_error, display):
    """
    Verifies that handle_process_invoice shows an error popup and does not invoke
    the process callback when no file has been selected.

    Args:
        mock_show_error (unittest.mock.MagicMock): Mocks show_error_popup
        display (pytest.fixture): Provides the display and its mocks
    """

    # No file has been selected in the entry widget
    display.display.selected_file.get.return_value = ""

    display.display.handle_process_invoice()

    # An error popup is shown and the callback is never called
    mock_show_error.assert_called_once()
    display.process_callback.assert_not_called()


@patch.object(InvoiceAppDisplay, "show_error_popup")
def test_handle_process_invoice_forwards_to_callback(mock_show_error, display):
    """
    Verifies that handle_process_invoice forwards the selected file to the
    process callback (with append_output False) when a file is selected.

    Args:
        mock_show_error (unittest.mock.MagicMock): Mocks show_error_popup
        display (pytest.fixture): Provides the display and its mocks
    """

    # A file has been selected in the entry widget
    display.display.selected_file.get.return_value = "C:/invoices/order.pdf"

    display.display.handle_process_invoice()

    # The callback processes the single invoice without appending, no error shown
    display.process_callback.assert_called_once_with(
        "C:/invoices/order.pdf", append_output=False
    )
    mock_show_error.assert_not_called()


###############################################################################
###         Tests InvoiceAppDisplay -> handle_process_all_invoices()        ###
###############################################################################
@patch("source.InvoiceAppDisplay.Path")
def test_handle_process_all_invoices_processes_each(mock_path, display):
    """
    Verifies that handle_process_all_invoices iterates the invoices directory and
    forwards each file to the process callback with append_output True.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        display (pytest.fixture): Provides the display and its mocks
    """

    # The invoices directory yields two invoice files
    first_invoice = MagicMock()
    second_invoice = MagicMock()
    mock_path.return_value.resolve.return_value.iterdir.return_value = [
        first_invoice,
        second_invoice,
    ]

    display.display.handle_process_all_invoices()

    # The directory is resolved from the configured invoices path
    mock_path.assert_called_once_with(INVOICES_PATH)

    # Each invoice is processed in order, appending to the running output
    display.process_callback.assert_has_calls(
        [
            call(first_invoice, append_output=True),
            call(second_invoice, append_output=True),
        ]
    )
    assert display.process_callback.call_count == 2


@patch.object(InvoiceAppDisplay, "show_error_popup")
@patch("source.InvoiceAppDisplay.Path")
def test_handle_process_all_invoices_error_shows_popup(
    mock_path, mock_show_error, display
):
    """
    Verifies that handle_process_all_invoices shows an error popup when iterating
    the invoices directory raises an exception.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        mock_show_error (unittest.mock.MagicMock): Mocks show_error_popup
        display (pytest.fixture): Provides the display and its mocks
    """

    # Resolving/iterating the invoices directory fails
    mock_path.return_value.resolve.return_value.iterdir.side_effect = OSError(
        "directory unavailable"
    )

    display.display.handle_process_all_invoices()

    # The failure is surfaced to the user via an error popup
    mock_show_error.assert_called_once()


###############################################################################
###              Tests InvoiceAppDisplay -> show_error_popup()              ###
###############################################################################
@patch("source.InvoiceAppDisplay.messagebox.showerror")
def test_show_error_popup_displays_message(mock_showerror, display):
    """
    Verifies that show_error_popup shows a messagebox error when not running in
    integration test mode.

    Args:
        mock_showerror (unittest.mock.MagicMock): Mocks messagebox.showerror
        display (pytest.fixture): Provides the display and its mocks
    """

    # Running with a visible GUI (not headless)
    display.arg_provider.integration_test_mode = False

    display.display.show_error_popup(
        error_title="Some Title", error_message="Some Message"
    )

    # The error is shown to the user
    mock_showerror.assert_called_once_with("Some Title", "Some Message")


@patch("source.InvoiceAppDisplay.messagebox.showerror")
def test_show_error_popup_suppressed_in_integration_mode(mock_showerror, display):
    """
    Verifies that show_error_popup suppresses the messagebox when running in
    integration test (headless) mode so automated runs do not block on a popup.

    Args:
        mock_showerror (unittest.mock.MagicMock): Mocks messagebox.showerror
        display (pytest.fixture): Provides the display and its mocks
    """

    # Running headless for integration testing
    display.arg_provider.integration_test_mode = True

    display.display.show_error_popup(
        error_title="Some Title", error_message="Some Message"
    )

    # No popup is shown in headless mode
    mock_showerror.assert_not_called()


###############################################################################
###                Tests InvoiceAppDisplay -> handle_clear()                ###
###############################################################################
def test_handle_clear_resets_state(display):
    """
    Verifies that handle_clear resets the selected file and clears the output box.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.handle_clear()

    # The selected file is reset and the output box is emptied
    display.display.selected_file.set.assert_called_once_with("")
    display.display.output_box.delete.assert_called_once_with(1.0, tk.END)


def test_handle_clear_no_output_box(display):
    """
    Verifies that handle_clear still resets the selected file and does not error
    when the output box has not been initialized.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    # Simulate the output box never having been built
    display.display.output_box = None

    display.display.handle_clear()

    # The selected file is still reset even without an output box
    display.display.selected_file.set.assert_called_once_with("")


###############################################################################
###      Tests InvoiceAppDisplay -> handle_*  (open config/log files)       ###
###############################################################################
@patch("source.InvoiceAppDisplay.open_in_system_editor")
def test_handle_cost_criteria_opens_config(mock_open_editor, display):
    """
    Verifies that handle_cost_criteria opens the cost criteria config file in the
    system editor.

    Args:
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.handle_cost_criteria()
    mock_open_editor.assert_called_once_with(COST_CRITERIA_PATH)


@patch("source.InvoiceAppDisplay.open_in_system_editor")
def test_handle_payment_terms_opens_config(mock_open_editor, display):
    """
    Verifies that handle_payment_terms opens the payment terms config file in the
    system editor.

    Args:
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.handle_payment_terms()
    mock_open_editor.assert_called_once_with(PAYMENT_TERMS_PATH)


@patch("source.InvoiceAppDisplay.open_in_system_editor")
def test_handle_sales_reps_opens_config(mock_open_editor, display):
    """
    Verifies that handle_sales_reps opens the sales reps config file in the
    system editor.

    Args:
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.handle_sales_reps()
    mock_open_editor.assert_called_once_with(SALES_REPS_PATH)


@patch("source.InvoiceAppDisplay.open_in_system_editor")
@patch("source.InvoiceAppDisplay.Path")
def test_handle_results_log_opens_when_present(mock_path, mock_open_editor, display):
    """
    Verifies that handle_results_log opens the results log when the file exists.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        display (pytest.fixture): Provides the display and its mocks
    """

    # The results log file exists on disk
    mock_path.return_value.exists.return_value = True

    display.display.handle_results_log()

    # The existing results log is opened in the system editor
    mock_path.assert_called_once_with(RESULTS_LOG_PATH)
    mock_open_editor.assert_called_once_with(RESULTS_LOG_PATH)


@patch.object(InvoiceAppDisplay, "show_error_popup")
@patch("source.InvoiceAppDisplay.open_in_system_editor")
@patch("source.InvoiceAppDisplay.Path")
def test_handle_results_log_missing_shows_error(
    mock_path, mock_open_editor, mock_show_error, display
):
    """
    Verifies that handle_results_log shows an error popup (and opens nothing) when
    the results log file does not exist yet.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        mock_show_error (unittest.mock.MagicMock): Mocks show_error_popup
        display (pytest.fixture): Provides the display and its mocks
    """

    # The results log file has not been created
    mock_path.return_value.exists.return_value = False

    display.display.handle_results_log()

    # An error popup is shown and nothing is opened
    mock_show_error.assert_called_once()
    mock_open_editor.assert_not_called()


@patch("source.InvoiceAppDisplay.open_in_system_editor")
@patch("source.InvoiceAppDisplay.Path")
def test_handle_debug_log_opens_when_present(mock_path, mock_open_editor, display):
    """
    Verifies that handle_debug_log opens the debug log when the file exists.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        display (pytest.fixture): Provides the display and its mocks
    """

    # The debug log file exists on disk
    mock_path.return_value.exists.return_value = True

    display.display.handle_debug_log()

    # The existing debug log is opened in the system editor
    mock_path.assert_called_once_with(DEBUG_LOG_PATH)
    mock_open_editor.assert_called_once_with(DEBUG_LOG_PATH)


@patch.object(InvoiceAppDisplay, "show_error_popup")
@patch("source.InvoiceAppDisplay.open_in_system_editor")
@patch("source.InvoiceAppDisplay.Path")
def test_handle_debug_log_missing_shows_error(
    mock_path, mock_open_editor, mock_show_error, display
):
    """
    Verifies that handle_debug_log shows an error popup (and opens nothing) when
    the debug log file does not exist yet.

    Args:
        mock_path (unittest.mock.MagicMock): Mocks the Path class
        mock_open_editor (unittest.mock.MagicMock): Mocks open_in_system_editor
        mock_show_error (unittest.mock.MagicMock): Mocks show_error_popup
        display (pytest.fixture): Provides the display and its mocks
    """

    # The debug log file has not been created
    mock_path.return_value.exists.return_value = False

    display.display.handle_debug_log()

    # An error popup is shown and nothing is opened
    mock_show_error.assert_called_once()
    mock_open_editor.assert_not_called()


###############################################################################
###                Tests InvoiceAppDisplay -> apply_theme()                 ###
###############################################################################
def test_apply_theme_updates_state_and_widgets(display):
    """
    Verifies that apply_theme stores the new theme and reconfigures the window
    and tracked widgets with that theme's colors.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.apply_theme(LIGHT)

    # The active theme is updated
    assert display.display.current_theme == LIGHT

    # The window background and a representative widget adopt the theme colors
    display.configure.assert_any_call(bg=LIGHT.bg_main)
    display.display.output_box.configure.assert_called_once_with(
        bg=LIGHT.bg_entry, fg=LIGHT.fg_text, insertbackground=LIGHT.fg_text
    )


###############################################################################
###             Tests InvoiceAppDisplay -> apply_font_family()              ###
###############################################################################
def test_apply_font_family_updates_state_and_widgets(display):
    """
    Verifies that apply_font_family stores the chosen family and applies the new
    font (family, size, weight) to the tracked widgets.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.apply_font_family("Arial")

    # The active font family is updated and applied to the widgets
    assert display.display.current_font_family == "Arial"
    display.display.title_label.configure.assert_called_once_with(
        font=("Arial", DEFAULT_FONT_SIZE, "bold")
    )


###############################################################################
###              Tests InvoiceAppDisplay -> apply_font_size()               ###
###############################################################################
def test_apply_font_size_updates_state_and_widgets(display):
    """
    Verifies that apply_font_size stores the chosen size and applies the new font
    (family, size, weight) to the tracked widgets.

    Args:
        display (pytest.fixture): Provides the display and its mocks
    """

    display.display.apply_font_size(20)

    # The active font size is updated and applied to the widgets
    assert display.display.current_font_size == 20
    display.display.output_box.configure.assert_called_once_with(
        font=(DEFAULT_FONT_FAMILY, 20, "bold")
    )
