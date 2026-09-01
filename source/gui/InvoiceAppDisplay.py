import tkinter as tk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, scrolledtext
from typing import Protocol

from fishbowl_common import ArgumentProvider, UpdateCheckResult
from fishbowl_common.gui import (
    ALL_THEMES,
    DARK,  # Default theme used by GUI
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    FONT_FAMILIES,
    FONT_SIZES,
    RED,  # Used for the EXIT button
    THEME_BY_NAME,
    AboutWindow,
    FileEditorWindow,
    MessageWindow,
    PatchNotesWindow,
    Theme,
    Tooltip,
    UpdateWindow,
)

from source.constants import (
    APP_NAME,
    COST_CRITERIA_PATH,
    DEBUG_LOG_PATH,
    INVOICES_DIR,
    PAYMENT_TERMS_PATH,
    RESULTS_LOG_PATH,
    SALES_REPS_PATH,
    SETTING_KEY_FONT_FAMILY,
    SETTING_KEY_FONT_SIZE,
    SETTING_KEY_THEME,
    USER_GUIDE_PATH,
    VERSION,
)
from source.gui.InvoiceDiscoveryWindow import InvoiceDiscoveryWindow
from source.Invoice import Invoice

# Future TODO: Add second output window for errors, instead of cluttering the screen with
#              pop up windows when Fishbowl invoices present rounding errors


# The invoice-processing callback the controller hands in. Declared as a Protocol
# rather than a Callable so append_output keeps its name: the call sites below pass
# it by keyword, which Callable[[Path, bool], None] cannot express.
class ProcessInvoiceCallback(Protocol):
    def __call__(self, invoice_filepath: Path, append_output: bool) -> None:
        """
        Processes one invoice PDF and displays its cost breakdown.

        Args:
            invoice_filepath: The invoice PDF to process
            append_output: Whether to append this invoice's output to what is already
                there, or replace it
        """


# Invoice App Display class to own the GUI for selecting and processing invoices
# This implementation uses tkinter for the GUI
class InvoiceAppDisplay(tk.Tk):
    ###########################################################################
    ###                   InvoiceAppDisplay -> __init__()                   ###
    ###########################################################################
    def __init__(
        self,
        process_callback: ProcessInvoiceCallback,
        read_file_callback: Callable[[Path], str],
        save_config_callback: Callable[[Path, str], None],
        save_settings_callback: Callable[[str, str], None],
        copy_invoice_callback: Callable[[Path, bool], str],
        check_for_updates_callback: Callable[[], None],
        view_patch_notes_callback: Callable[[], None],
        title: str,
        window_resolution: str,
        settings: dict[str, str] | None = None,
    ) -> None:
        """
        Initializes the InvoiceAppDisplay object

        Args:
            process_callback: Callback that processes the selected invoice file and
                displays its cost breakdown
            read_file_callback: Callback that reads a file's full contents, used to
                populate the native file editor/viewer window
            save_config_callback: Callback that persists edited config contents (and
                reloads them), invoked when the user saves
            save_settings_callback: Callback that persists a single user setting (key,
                value), invoked when the user changes a theme/font/font-size preference
            copy_invoice_callback: Callback that copies a selected invoice PDF (source
                path, overwrite flag) into the Invoices/ folder, used by the Invoice
                Discovery window. Returns "copied", "exists", or "error"
            check_for_updates_callback: Callback that triggers an on-demand update check,
                invoked when the user selects "Check for Updates" from the Help menu
            view_patch_notes_callback: Callback that shows the patch notes, invoked when
                the user selects "What's New" from the Help menu
            title: Title of the application window
            window_resolution: Resolution of the application window (e.g., "750x750")
            settings: Previously persisted settings (theme/font/font-size) used to restore
                the user's last choices on startup. Missing or unknown values fall back to
                the application defaults.
        """

        super().__init__()

        # Argument provider, needed to check for integration test mode so that popups can be suppressed
        # to run headless during automated testing
        self.argument_provider = ArgumentProvider()

        # Title applied to the application window
        self.title(title)

        # Resolution of the application window
        self.geometry(window_resolution)

        # Allow user to resize window in x and y direction
        self.resizable(True, True)

        # Holds the last selected invoice filepath
        self.selected_file = tk.StringVar()

        # Callback function to process the selected invoice file
        self.process_callback = process_callback

        # Callback to read a file's contents for the native editor/viewer window
        self.read_file_callback = read_file_callback

        # Callback to persist (and reload) edited config file contents
        self.save_config_callback = save_config_callback

        # Callback to persist a single changed user setting (theme/font/size)
        self.save_settings_callback = save_settings_callback

        # Callback to copy a selected invoice into the Invoices/ folder, used by
        # the Invoice Discovery window
        self.copy_invoice_callback = copy_invoice_callback

        # Callback to trigger an on-demand update check from the Help menu
        self.check_for_updates_callback = check_for_updates_callback

        # Callback to show the patch notes on demand from the Help menu
        self.view_patch_notes_callback = view_patch_notes_callback

        # Restore the user's last-chosen settings, falling back to the defaults
        # for anything missing or unrecognized. These are set before build_widgets()
        # so every widget is created already using the restored theme and font.
        settings = settings or {}
        self.current_theme = THEME_BY_NAME.get(settings.get(SETTING_KEY_THEME), DARK)
        self.current_font_family = settings.get(SETTING_KEY_FONT_FAMILY, DEFAULT_FONT_FAMILY)
        self.current_font_size = self._parse_font_size(settings.get(SETTING_KEY_FONT_SIZE))

        # Tkinter Widgets. Declared without a value rather than as `| None = None`:
        # build_widgets() is the last statement in this constructor and creates
        # every one of them, so nothing can observe one unset and no method below
        # needs to guard against None.
        # fmt:off
        self.menu_bar:                    tk.Menu
        self.file_menu:                   tk.Menu
        self.edit_menu:                   tk.Menu
        self.view_menu:                   tk.Menu
        self.preferences_menu:            tk.Menu
        self.help_menu:                   tk.Menu
        self.title_label:                 tk.Label
        self.file_frame:                  tk.Frame
        self.file_entry:                  tk.Entry
        self.browse_button:               tk.Button
        self.button_frame:                tk.Frame
        self.process_invoice_button:      tk.Button
        self.exit_button:                 tk.Button
        self.process_all_invoices_button: tk.Button
        self.discover_invoices_button:    tk.Button
        self.output_label:                tk.Label
        self.output_box:                  scrolledtext.ScrolledText
        # fmt:on

        # Hover tooltips attached to the buttons, kept so they can be restyled
        # when the user changes the theme or font at runtime
        self.tooltips: list[Tooltip] = []

        # Build the GUI
        self.build_widgets()

    ###########################################################################
    ###                InvoiceAppDisplay -> build_widgets()                 ###
    ###########################################################################
    def build_widgets(self) -> None:  # noqa: PLR0915
        """
        Creates the GUI widgets for the application
        This includes a title label, file selection entry, browse button, and action buttons
        """

        self.configure(bg=self.current_theme.bg_main)

        # Menu bar containing dropdowns for File, Edit, and Preferences
        self.menu_bar = tk.Menu(self)

        # File dropdown
        #  -> Open option to open a single invoice
        #  -> Clear option to clear the output box and reset the selected file
        #  -> Exit option to close the application
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.handle_browse_button)
        self.file_menu.add_command(label="Clear", command=self.handle_clear)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # Edit dropdown
        #  -> Cost Criteria option to open the cost criteria config file in the default text editor for user editing
        self.edit_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.edit_menu.add_command(label="Cost Criteria", command=self.handle_cost_criteria)
        self.edit_menu.add_command(label="Payment Terms", command=self.handle_payment_terms)
        self.edit_menu.add_command(label="Sales Reps", command=self.handle_sales_reps)
        self.menu_bar.add_cascade(label="Edit", menu=self.edit_menu)

        # View dropdown
        #  -> Results Log option to open the results log file
        #  -> Debug Log option to open the debug log file (only in debug configuration)
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="Results Log", command=self.handle_results_log)
        if __debug__:
            self.view_menu.add_command(label="Debug Log", command=self.handle_debug_log)
        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

        # Preferences dropdown
        #  -> Theme option to select from available color themes
        #  -> Font option to select the font family used throughout the application
        #  -> Font Size option to adjust the text size throughout the application
        self.preferences_menu = tk.Menu(self.menu_bar, tearoff=0)

        theme_menu = tk.Menu(self.preferences_menu, tearoff=0)
        for theme_option in ALL_THEMES:
            theme_menu.add_command(
                label=theme_option.name,
                command=lambda t=theme_option: self.apply_theme(t),
            )
        self.preferences_menu.add_cascade(label="Theme", menu=theme_menu)

        font_menu = tk.Menu(self.preferences_menu, tearoff=0)
        for family in FONT_FAMILIES:
            font_menu.add_command(
                label=family,
                command=lambda f=family: self.apply_font_family(f),
            )
        self.preferences_menu.add_cascade(label="Font", menu=font_menu)

        font_size_menu = tk.Menu(self.preferences_menu, tearoff=0)
        for size in FONT_SIZES:
            font_size_menu.add_command(
                label=str(size),
                command=lambda s=size: self.apply_font_size(s),
            )
        self.preferences_menu.add_cascade(label="Font Size", menu=font_size_menu)

        self.menu_bar.add_cascade(label="Preferences", menu=self.preferences_menu)

        # Help dropdown
        #  -> About option to show the current application version
        #  -> Check for Updates option to manually check for a newer release
        #  -> Open User Guide option to view the bundled USER_GUIDE.txt in-app
        #  -> What's New option to re-read the bundled patch notes at any time
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.help_menu.add_command(label="About", command=self.handle_about)
        self.help_menu.add_command(label="Check for Updates", command=self.handle_check_for_updates)
        self.help_menu.add_command(label="Open User Guide", command=self.handle_open_user_guide)
        self.help_menu.add_command(label="What's New", command=self.handle_view_patch_notes)
        self.menu_bar.add_cascade(label="Help", menu=self.help_menu)

        # Configure the menu bar
        self.config(menu=self.menu_bar)

        # Title Label
        self.title_label = tk.Label(
            self,
            text="Choose a Fishbowl Invoice PDF to Process",
            font=(self.current_font_family, self.current_font_size, "bold"),
            bg=self.current_theme.bg_main,
            fg=self.current_theme.label_fg,
        )
        self.title_label.pack(pady=(20, 10))

        # File selection frame
        self.file_frame = tk.Frame(self, bg=self.current_theme.bg_main)
        self.file_frame.pack(padx=20, fill="x")

        self.file_entry = tk.Entry(
            self.file_frame,
            textvariable=self.selected_file,
            state="readonly",
            width=50,
            bg=self.current_theme.bg_entry,
            fg=self.current_theme.bg_main,
            insertbackground=self.current_theme.fg_text,
            relief="flat",
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=8)

        # Browse button to open file dialog
        self.browse_button = tk.Button(
            self.file_frame,
            text="Browse",
            command=self.handle_browse_button,
            bg=self.current_theme.button_bg,
            fg=self.current_theme.button_fg,
            activebackground=self.current_theme.accent,
            activeforeground=self.current_theme.fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.browse_button.pack(side="left", padx=(10, 0), pady=8)

        # Action buttons frame
        self.button_frame = tk.Frame(self, bg=self.current_theme.bg_main)
        self.button_frame.pack(pady=20)

        # Create button for processing a single invoice
        self.process_invoice_button = tk.Button(
            self.button_frame,
            text="Process This Invoice",
            command=self.handle_process_invoice,
            bg=self.current_theme.button_bg,
            fg=self.current_theme.button_fg,
            activebackground=self.current_theme.accent,
            activeforeground=self.current_theme.fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.process_invoice_button.grid(row=0, column=0, padx=10)

        # Create button for exiting the application. Placed on its own row below
        # the three action buttons and spanning all three columns so it stays
        # centered beneath them.
        self.exit_button = tk.Button(
            self.button_frame,
            text="Exit",
            command=self.quit,
            bg=self.current_theme.bg_entry,
            fg=self.current_theme.fg_text,
            activebackground=RED,
            activeforeground=self.current_theme.fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.exit_button.grid(row=1, column=0, columnspan=3, pady=(10, 0))

        # Create button for processing all invoices in the Invoices folder at once
        self.process_all_invoices_button = tk.Button(
            self.button_frame,
            text="Process All Invoices",
            command=self.handle_process_all_invoices,
            bg=self.current_theme.button_bg,
            fg=self.current_theme.button_fg,
            activebackground=self.current_theme.accent,
            activeforeground=self.current_theme.fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.process_all_invoices_button.grid(row=0, column=1, padx=10)

        # Create button for discovering invoices: copying downloaded invoice PDFs
        # into the Invoices/ folder from within the app
        self.discover_invoices_button = tk.Button(
            self.button_frame,
            text="Discover Invoices",
            command=self.handle_discover_invoices,
            bg=self.current_theme.button_bg,
            fg=self.current_theme.button_fg,
            activebackground=self.current_theme.accent,
            activeforeground=self.current_theme.fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.discover_invoices_button.grid(row=0, column=2, padx=10)

        # Output Label before text results
        self.output_label = tk.Label(
            self,
            text="Output:",
            font=(self.current_font_family, self.current_font_size, "bold"),
            bg=self.current_theme.bg_main,
            fg=self.current_theme.label_fg,
        )
        self.output_label.pack(anchor="w", padx=22, pady=(0, 2))

        # Output box to display invoice results
        self.output_box = scrolledtext.ScrolledText(
            self,
            height=8,
            wrap="word",
            font=(self.current_font_family, self.current_font_size, "bold"),
            bg=self.current_theme.bg_entry,
            fg=self.current_theme.fg_text,
            insertbackground=self.current_theme.fg_text,
            relief="flat",
        )
        self.output_box.pack(padx=20, pady=(0, 10), fill="both", expand=True)

        # Attach hover tooltips describing what each button does
        self._attach_tooltip(
            self.browse_button,
            "Open a file dialog to choose an invoice PDF to process",
        )
        self._attach_tooltip(
            self.process_invoice_button,
            "Process the selected invoice and show its cost breakdown",
        )
        self._attach_tooltip(
            self.process_all_invoices_button,
            "Process every invoice PDF in the Invoices/ folder",
        )
        self._attach_tooltip(
            self.discover_invoices_button,
            "Copy downloaded invoice PDFs into the Invoices/ folder",
        )
        self._attach_tooltip(self.exit_button, "Close the application")

    ###########################################################################
    ###               InvoiceAppDisplay -> _attach_tooltip()               ###
    ###########################################################################
    def _attach_tooltip(self, widget: tk.Widget, text: str) -> None:
        """
        Attaches a hover tooltip to a widget, styled with the active theme/font,
        and tracks it so it can be restyled when the theme or font changes.

        Args:
            widget: The widget that shows the tooltip when hovered
            text: The informational text to display on hover
        """
        self.tooltips.append(
            Tooltip(
                widget=widget,
                text=text,
                theme=self.current_theme,
                font_family=self.current_font_family,
                font_size=self.current_font_size,
            )
        )

    ###########################################################################
    ###               InvoiceAppDisplay -> _refresh_tooltips()             ###
    ###########################################################################
    def _refresh_tooltips(self) -> None:
        """
        Restyles every attached tooltip with the current theme and font so the
        tooltips stay consistent after a theme or font change.
        """
        for tooltip in self.tooltips:
            tooltip.update_style(
                self.current_theme,
                self.current_font_family,
                self.current_font_size,
            )

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_browse_button()             ###
    ###########################################################################
    def handle_browse_button(self) -> None:
        """
        On "Browse" button press, opens a file dialog to select a PDF invoice file.
        Once selected, the file is set to the selected_file member variable

        """

        # Open a file dialog to select a PDF invoice file (Tk requires a str path)
        file_path = filedialog.askopenfilename(
            initialdir=str(INVOICES_DIR),
            title="Select Invoice PDF",
            filetypes=[("PDF files", "*.pdf")],  # Filter for PDF files only
        )

        # If a valid filepath was selected, update the selected_file variable
        if file_path:
            self.selected_file.set(file_path)

    ###########################################################################
    ###            InvoiceAppDisplay -> display_invoice_output()            ###
    ###########################################################################
    def display_invoice_output(self, invoice: Invoice, append_output: bool = False) -> None:
        """
        Displays the calculated totals of the invoice in the output box

        Args:
            invoice: The processed invoice containing calculated totals
            append_output: Whether to append to the output box or clear it first before
                writing. Defaults to False, meaning the output box will be cleared
                before writing
        """

        # Clear the output box if not appending
        if not append_output:
            self.output_box.delete(1.0, tk.END)

        # If appending, separate this invoice from the one above it
        else:
            self.output_box.insert(tk.END, "\n")

        self.output_box.insert(tk.END, invoice.to_formatted_string())

    ###########################################################################
    ###            InvoiceAppDisplay -> handle_process_invoice()            ###
    ###########################################################################
    def handle_process_invoice(self) -> None:
        """
        On "Process This Invoice" button press, processes the selected PDF invoice file
        by forwarding the call to the provided process_callback function specified during construction
        """

        # Try to use the last selected file from the file dialogue widget
        file_path = self.selected_file.get()

        # If no file is selected, show an error popup and do nothing
        if not file_path:
            self.show_popup(
                title="No file selected",
                message="Please select a PDF file first.",
            )
            return

        # Forward the call to the process_callback function with the selected file path as a Path.
        # Append output is false to reset the output windows and results.txt file since this is the
        # only invoice being processed
        self.process_callback(Path(file_path), append_output=False)

    ###########################################################################
    ###         InvoiceAppDisplay -> handle_process_all_invoices()          ###
    ###########################################################################
    def handle_process_all_invoices(self) -> None:
        """
        On "Process All Invoices" button press, processes all invoice PDF files in the specified invoices directory
        by iterating through each file and calling the process_callback function for each one.
        This will append the output to the results.txt file and output widget.
        """

        try:
            # Loop through all invoice files in the invoices directory and process each one
            for file_path in INVOICES_DIR.resolve().iterdir():
                # Process each invoice, appending output to the results.txt file and output widget
                self.process_callback(file_path, append_output=True)

        # BLE001 is suppressed rather than satisfied: this is the GUI's outer
        # boundary over a directory of arbitrary user-supplied PDFs. A parse
        # failure must reach the user as a popup rather than an unhandled crash,
        # so the catch stays broad here even though every handler beneath this
        # layer is narrow.
        except Exception as e:  # noqa: BLE001
            self.show_popup(
                title="Processing Error",
                message=f"An error occurred while processing invoices: {e}",
            )

    ###########################################################################
    ###          InvoiceAppDisplay -> handle_discover_invoices()            ###
    ###########################################################################
    def handle_discover_invoices(self) -> None:
        """
        On "Discover Invoices" button press, opens the Invoice Discovery window so
        the user can copy downloaded invoice PDFs into the Invoices/ folder
        without leaving the application.
        """
        InvoiceDiscoveryWindow(
            parent=self,
            title="Discover Invoices",
            theme=self.current_theme,
            font_family=self.current_font_family,
            font_size=self.current_font_size,
            copy_callback=self.copy_invoice_callback,
        )

    ###########################################################################
    ###                 InvoiceAppDisplay -> handle_about()                 ###
    ###########################################################################
    def handle_about(self) -> None:
        """
        On "About" menu press, opens the About window showing the current
        application version, themed to match the rest of the application.
        """
        AboutWindow(
            parent=self,
            title="About",
            app_name=APP_NAME,
            version=VERSION,
            theme=self.current_theme,
            font_family=self.current_font_family,
            font_size=self.current_font_size,
        )

    ###########################################################################
    ###          InvoiceAppDisplay -> handle_check_for_updates()            ###
    ###########################################################################
    def handle_check_for_updates(self) -> None:
        """
        On "Check for Updates" menu press, asks the controller to run an on-demand
        update check. The controller surfaces the outcome back through
        show_update_available() / show_popup().
        """
        self.check_for_updates_callback()

    ###########################################################################
    ###            InvoiceAppDisplay -> handle_open_user_guide()            ###
    ###########################################################################
    def handle_open_user_guide(self) -> None:
        """
        On "Open User Guide" menu press, opens the bundled user guide in a native
        read-only viewer window, themed to match the rest of the application.
        """
        # The user guide is longer than the config/log files, so open it in a
        # larger window so more of the text is visible without scrolling
        self._open_readonly_file_viewer(
            USER_GUIDE_PATH,
            "User Guide",
            f"User guide not found at: {USER_GUIDE_PATH}.",
            text_width=100,
            text_height=35,
        )

    ###########################################################################
    ###           InvoiceAppDisplay -> handle_view_patch_notes()            ###
    ###########################################################################
    def handle_view_patch_notes(self) -> None:
        """
        On "What's New" menu press, asks the controller for the patch notes. The
        controller reads them and hands them back through show_patch_notes(), so
        the display never reads a file of its own.
        """
        self.view_patch_notes_callback()

    ###########################################################################
    ###              InvoiceAppDisplay -> show_patch_notes()                ###
    ###########################################################################
    def show_patch_notes(self, app_name: str, version: str, notes: str) -> None:
        """
        Shows the user what changed, in a themed window matching the rest of the
        application. Called by the controller both on the first launch after an
        update and from the Help menu, which is why the notes arrive as a string
        the controller has already selected.

        Args:
            app_name: The application name to display in the heading
            version: The version whose notes are being announced
            notes: The notes to display, already selected by the controller
        """
        PatchNotesWindow(
            parent=self,
            title="What's New",
            app_name=app_name,
            version=version,
            notes=notes,
            theme=self.current_theme,
            font_family=self.current_font_family,
            font_size=self.current_font_size,
        )

    ###########################################################################
    ###                  InvoiceAppDisplay -> show_popup()                  ###
    ###########################################################################
    def show_popup(self, title: str, message: str) -> None:
        """
        Displays a message (informational or error) in a popup window

        Args:
            title: The title of the popup
            message: The message to display
        """

        # If in integration test mode, do not show popups since this will be running
        # in a headless environment, and will halt testing
        if self.argument_provider.integration_test_mode:
            return

        # Use a themed window (rather than tkinter's native messagebox) so the
        # popup matches the application's styling and centers over the application
        # window instead of the screen
        MessageWindow(
            parent=self,
            title=title,
            message=message,
            theme=self.current_theme,
            font_family=self.current_font_family,
            font_size=self.current_font_size,
        )

    ###########################################################################
    ###            InvoiceAppDisplay -> show_update_available()             ###
    ###########################################################################
    def show_update_available(
        self,
        result: UpdateCheckResult,
        start_install: (Callable[[Callable[[int, int], None], Callable[[bool], None]], None] | None) = None,
    ) -> None:
        """
        Notifies the user that a newer release is available by opening a themed
        popup showing the available version, with an "Exit and Update" button that
        opens the release page and closes the app, and a Close button. When the
        release can be installed in place, the window also offers an "Update and
        Restart" button driven by start_install.

        The controller calls this on the GUI thread when an update check (on
        startup or triggered manually from the Help menu) finds a strictly newer
        release.

        Args:
            result: The outcome of the update check, exposing the newer release's
                `latest_version` and `release_url`.
            start_install: Downloads and starts this release's installer, taking a
                progress callback and a completion callback. None when the release cannot
                be installed in place, which leaves the window offering only the manual
                download.
        """

        # If in integration test mode, do not show popups since this will be running
        # in a headless environment, and will halt testing
        if self.argument_provider.integration_test_mode:
            return

        UpdateWindow(
            parent=self,
            title="Update Available",
            latest_version=result.latest_version,
            release_url=result.release_url,
            # self is the root tk.Tk, so destroy() exits the whole app, releasing
            # the executable's file lock so the installer can replace it
            close_app_callback=self.destroy,
            theme=self.current_theme,
            font_family=self.current_font_family,
            font_size=self.current_font_size,
            start_install_callback=start_install,
        )

    ###########################################################################
    ###                 InvoiceAppDisplay -> handle_clear()                 ###
    ###########################################################################
    def handle_clear(self) -> None:
        """
        Clears the output box and resets the selected file path
        """
        self.selected_file.set("")
        self.output_box.delete(1.0, tk.END)

    ###########################################################################
    ###            InvoiceAppDisplay -> _open_config_editor()               ###
    ###########################################################################
    def _open_config_editor(self, config_path: Path, title: str) -> None:
        """
        Opens a native, editable window for the given config file, prefilled with
        its current contents and wired to persist edits via the save callback

        Args:
            config_path: The config file to open for editing
            title: The title to display on the editor window
        """
        FileEditorWindow(
            parent=self,
            title=title,
            file_path=config_path,
            initial_text=self.read_file_callback(config_path),
            theme=self.current_theme,
            font_family=self.current_font_family,
            font_size=self.current_font_size,
            editable=True,
            save_callback=self.save_config_callback,
        )

    ###########################################################################
    ###           InvoiceAppDisplay -> _open_readonly_file_viewer()         ###
    ###########################################################################
    def _open_readonly_file_viewer(
        self,
        file_path: Path,
        title: str,
        missing_message: str,
        text_width: int | None = None,
        text_height: int | None = None,
    ) -> None:
        """
        Opens a native, read-only window showing the given text file if it exists.
        Shows an error popup with the provided message if the file is not present.

        Args:
            file_path: The text file to open for viewing
            title: The title to display on the viewer window
            missing_message: The popup message shown when the file does not exist
            text_width: Width of the text box in character cells, or None to use the
                default size (used to enlarge the viewer for longer files such as the user
                guide)
            text_height: Height of the text box in character cells, or None to use the
                default size
        """
        if file_path.exists():
            FileEditorWindow(
                parent=self,
                title=title,
                file_path=file_path,
                initial_text=self.read_file_callback(file_path),
                theme=self.current_theme,
                font_family=self.current_font_family,
                font_size=self.current_font_size,
                editable=False,
                text_width=text_width,
                text_height=text_height,
            )
        else:
            self.show_popup(
                title="File Not Found",
                message=missing_message,
            )

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_cost_criteria()             ###
    ###########################################################################
    def handle_cost_criteria(self) -> None:
        """
        Opens the Cost Criteria config file in a native editor window
        """
        self._open_config_editor(COST_CRITERIA_PATH, "Cost Criteria")

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_payment_terms()             ###
    ###########################################################################
    def handle_payment_terms(self) -> None:
        """
        Opens the Payment Terms config file in a native editor window
        """
        self._open_config_editor(PAYMENT_TERMS_PATH, "Payment Terms")

    ###########################################################################
    ###              InvoiceAppDisplay -> handle_sales_reps()               ###
    ###########################################################################
    def handle_sales_reps(self) -> None:
        """
        Opens the Sales Reps config file in a native editor window
        """
        self._open_config_editor(SALES_REPS_PATH, "Sales Reps")

    ###########################################################################
    ###              InvoiceAppDisplay -> handle_results_log()              ###
    ###########################################################################
    def handle_results_log(self) -> None:
        """
        Opens the results log file in a native read-only viewer window if it
        exists. Shows an error popup if the file has not been created yet.
        """
        self._open_readonly_file_viewer(
            RESULTS_LOG_PATH,
            "Results Log",
            f"Log not found at: {RESULTS_LOG_PATH}. Process an invoice to generate the log.",
        )

    ###########################################################################
    ###               InvoiceAppDisplay -> handle_debug_log()               ###
    ###########################################################################
    def handle_debug_log(self) -> None:
        """
        Opens the debug log file in a native read-only viewer window if it exists.
        Shows an error popup if the file has not been created yet.
        """
        self._open_readonly_file_viewer(
            DEBUG_LOG_PATH,
            "Debug Log",
            f"Log not found at: {DEBUG_LOG_PATH}. Process an invoice to generate the log.",
        )

    ###########################################################################
    ###                 InvoiceAppDisplay -> apply_theme()                  ###
    ###########################################################################
    def apply_theme(self, theme: Theme) -> None:
        """
        Applies a color theme to all widgets in the application

        Args:
            theme: The theme to apply
        """
        self.current_theme = theme

        self.configure(bg=theme.bg_main)
        self.title_label.configure(bg=theme.bg_main, fg=theme.label_fg)
        self.file_frame.configure(bg=theme.bg_main)
        self.file_entry.configure(bg=theme.bg_entry, fg=theme.bg_main, insertbackground=theme.fg_text)
        self.browse_button.configure(
            bg=theme.button_bg,
            fg=theme.button_fg,
            activebackground=theme.accent,
            activeforeground=theme.fg_text,
        )
        self.button_frame.configure(bg=theme.bg_main)
        self.process_invoice_button.configure(
            bg=theme.button_bg,
            fg=theme.button_fg,
            activebackground=theme.accent,
            activeforeground=theme.fg_text,
        )
        self.exit_button.configure(
            bg=theme.bg_entry,
            fg=theme.fg_text,
            activeforeground=theme.fg_text,
        )
        self.process_all_invoices_button.configure(
            bg=theme.button_bg,
            fg=theme.button_fg,
            activebackground=theme.accent,
            activeforeground=theme.fg_text,
        )
        self.discover_invoices_button.configure(
            bg=theme.button_bg,
            fg=theme.button_fg,
            activebackground=theme.accent,
            activeforeground=theme.fg_text,
        )
        self.output_label.configure(bg=theme.bg_main, fg=theme.label_fg)
        self.output_box.configure(bg=theme.bg_entry, fg=theme.fg_text, insertbackground=theme.fg_text)

        # Keep the hover tooltips consistent with the new theme
        self._refresh_tooltips()

        # Persist the choice so it is restored on the next launch
        self.save_settings_callback(SETTING_KEY_THEME, theme.name)

    ###########################################################################
    ###              InvoiceAppDisplay -> apply_font_family()               ###
    ###########################################################################
    def apply_font_family(self, family: str) -> None:
        """
        Applies a font family to all text on screen

        Args:
            family: The font family to apply
        """
        self.current_font_family = family
        self._apply_font()

        # Persist the choice so it is restored on the next launch
        self.save_settings_callback(SETTING_KEY_FONT_FAMILY, family)

    ###########################################################################
    ###               InvoiceAppDisplay -> apply_font_size()                ###
    ###########################################################################
    def apply_font_size(self, size: int) -> None:
        """
        Applies a font size to all text on screen

        Args:
            size: The font size to apply
        """
        self.current_font_size = size
        self._apply_font()

        # Persist the choice so it is restored on the next launch. Settings are
        # stored as strings, so the size is converted on the way out.
        self.save_settings_callback(SETTING_KEY_FONT_SIZE, str(size))

    ###########################################################################
    ###               InvoiceAppDisplay -> _parse_font_size()               ###
    ###########################################################################
    def _parse_font_size(self, value: str | None) -> int:
        """
        Converts a persisted font size value into an int, falling back to the
        default when it is missing or not a valid integer.

        Args:
            value: The raw font size loaded from settings, or None when no size has been
                persisted yet

        Returns:
            The restored font size, or DEFAULT_FONT_SIZE if value is missing or
            non-numeric.
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            return DEFAULT_FONT_SIZE

    ###########################################################################
    ###                 InvoiceAppDisplay -> _apply_font()                  ###
    ###########################################################################
    def _apply_font(self) -> None:
        """
        Applies the current font family and size to all text on screen
        """
        font = (self.current_font_family, self.current_font_size, "bold")
        self.title_label.configure(font=font)
        self.browse_button.configure(font=font)
        self.process_invoice_button.configure(font=font)
        self.exit_button.configure(font=font)
        self.process_all_invoices_button.configure(font=font)
        self.discover_invoices_button.configure(font=font)
        self.output_label.configure(font=font)
        self.output_box.configure(font=font)

        # Keep the hover tooltips consistent with the new font
        self._refresh_tooltips()
