import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Callable

from source.Invoice import Invoice
from source.ArgumentProvider import ArgumentProvider
from source.FileEditorWindow import FileEditorWindow
from source.color_theme import (
    ALL_THEMES,
    DARK,
    RED,
    THEME_BY_NAME,
    Theme,
)
from source.font_settings import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    FONT_FAMILIES,
    FONT_SIZES,
)
from source.constants import (
    INVOICES_PATH,
    PAYMENT_TERMS_PATH,
    SALES_REPS_PATH,
    COST_CRITERIA_PATH,
    RESULTS_LOG_PATH,
    DEBUG_LOG_PATH,
    SETTING_KEY_THEME,
    SETTING_KEY_FONT_FAMILY,
    SETTING_KEY_FONT_SIZE,
)

# Future TODO: Add second output window for errors, instead of cluttering the screen with
#              pop up windows when Fishbowl invoices present rounding errors


# Invoice App Display class to own the GUI for selecting and processing invoices
# This implementation uses tkinter for the GUI
class InvoiceAppDisplay(tk.Tk):

    ###########################################################################
    ###                   InvoiceAppDisplay -> __init__()                   ###
    ###########################################################################
    def __init__(
        self,
        process_callback,
        read_file_callback: Callable[[Path], str],
        save_config_callback: Callable[[Path, str], None],
        save_settings_callback: Callable[[str, str], None],
        title: str,
        window_resolution: str,
        settings: dict | None = None,
    ):
        """
        Initializes the InvoiceAppDisplay object

        Args:
            process_callback (callable): Callback function to process the selected invoice file
            read_file_callback (Callable[[Path], str]): Callback that reads a file's
                full contents, used to populate the native file editor/viewer window
            save_config_callback (Callable[[Path, str], None]): Callback that persists
                edited config contents (and reloads them), invoked when the user saves
            save_settings_callback (Callable[[str, str], None]): Callback that persists
                a single user setting (key, value), invoked when the user changes a
                theme/font/font-size preference
            title (str): Title of the application window
            window_resolution (str): Resolution of the application window (e.g., "750x750")
            settings (dict | None): Previously persisted settings (theme/font/font-size)
                used to restore the user's last choices on startup. Missing or unknown
                values fall back to the application defaults.
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

        # Restore the user's last-chosen settings, falling back to the defaults
        # for anything missing or unrecognized. These are set before build_widgets()
        # so every widget is created already using the restored theme and font.
        settings = settings or {}
        self.current_theme = THEME_BY_NAME.get(
            settings.get(SETTING_KEY_THEME), DARK
        )
        self.current_font_family = settings.get(
            SETTING_KEY_FONT_FAMILY, DEFAULT_FONT_FAMILY
        )
        self.current_font_size = self._parse_font_size(
            settings.get(SETTING_KEY_FONT_SIZE)
        )

        # Tkinter Widgets
        # fmt:off
        self.menu_bar:                    tk.Menu                    | None = None
        self.file_menu:                   tk.Menu                    | None = None
        self.edit_menu:                   tk.Menu                    | None = None
        self.view_menu:                   tk.Menu                    | None = None
        self.preferences_menu:            tk.Menu                    | None = None
        self.title_label:                 tk.Label                   | None = None
        self.file_frame:                  tk.Frame                   | None = None
        self.file_entry:                  tk.Entry                   | None = None
        self.browse_button:               tk.Button                  | None = None
        self.button_frame:                tk.Frame                   | None = None
        self.process_invoice_button:      tk.Button                  | None = None
        self.exit_button:                 tk.Button                  | None = None
        self.process_all_invoices_button: tk.Button                  | None = None
        self.output_label:                tk.Label                   | None = None
        self.output_box:                  scrolledtext.ScrolledText  | None = None
        # fmt:on

        # Build the GUI
        self.build_widgets()

    ###########################################################################
    ###                InvoiceAppDisplay -> build_widgets()                 ###
    ###########################################################################
    def build_widgets(self):
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
        self.edit_menu.add_command(
            label="Cost Criteria", command=self.handle_cost_criteria
        )
        self.edit_menu.add_command(
            label="Payment Terms", command=self.handle_payment_terms
        )
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

        self.preferences_menu.add_separator()
        self.preferences_menu.add_command(label="Settings")
        self.menu_bar.add_cascade(label="Preferences", menu=self.preferences_menu)

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

        # Create button for exiting the application
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
        self.exit_button.grid(row=0, column=1, padx=10)

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
        self.process_all_invoices_button.grid(row=0, column=2, padx=10)

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

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_browse_button()             ###
    ###########################################################################
    def handle_browse_button(self):
        """
        On "Browse" button press, opens a file dialog to select a PDF invoice file.
        Once selected, the file is set to the selected_file member variable

        """

        # Open a file dialog to select a PDF invoice file (Tk requires a str path)
        file_path = filedialog.askopenfilename(
            initialdir=str(INVOICES_PATH),
            title="Select Invoice PDF",
            filetypes=[("PDF files", "*.pdf")],  # Filter for PDF files only
        )

        # If a valid filepath was selected, update the selected_file variable
        if file_path:
            self.selected_file.set(file_path)

    ###########################################################################
    ###            InvoiceAppDisplay -> display_invoice_output()            ###
    ###########################################################################
    def display_invoice_output(self, invoice: Invoice, append_output: bool = False):
        """
        Displays the calculated totals of the invoice in the output box

        Args:
            invoice (Invoice): The processed invoice containing calculated totals
            append_output (bool): Whether to append to the output box or clear it first before writing
                                    Defaults to False, meaning the output box will be cleared before writing
        """

        # Clear the output box if not appending
        if not append_output:
            # Make sure output box was initialized before trying to clear it
            if self.output_box:
                self.output_box.delete(1.0, tk.END)
                self.output_box.insert(tk.END, invoice.to_formatted_string())

        # If appending, insert a newline before adding the new output
        else:
            # Make sure output_box was initialized before trying to insert
            if self.output_box:
                self.output_box.insert(tk.END, "\n")
                self.output_box.insert(tk.END, invoice.to_formatted_string())

    ###########################################################################
    ###            InvoiceAppDisplay -> handle_process_invoice()            ###
    ###########################################################################
    def handle_process_invoice(self):
        """
        On "Process This Invoice" button press, processes the selected PDF invoice file
        by forwarding the call to the provided process_callback function specified during construction
        """

        # Try to use the last selected file from the file dialogue widget
        file_path = self.selected_file.get()

        # If no file is selected, show an error popup and do nothing
        if not file_path:
            self.show_error_popup(
                error_title="No file selected",
                error_message="Please select a PDF file first.",
            )
            return

        # Forward the call to the process_callback function with the selected file path as a Path.
        # Append output is false to reset the output windows and results.txt file since this is the
        # only invoice being processed
        self.process_callback(Path(file_path), append_output=False)

    ###########################################################################
    ###         InvoiceAppDisplay -> handle_process_all_invoices()          ###
    ###########################################################################
    def handle_process_all_invoices(self):
        """
        On "Process All Invoices" button press, processes all invoice PDF files in the specified invoices directory
        by iterating through each file and calling the process_callback function for each one.
        This will append the output to the results.txt file and output widget.
        """

        try:
            # Loop through all invoice files in the invoices directory and process each one
            for file_path in INVOICES_PATH.resolve().iterdir():

                # Process each invoice, appending output to the results.txt file and output widget
                self.process_callback(file_path, append_output=True)

        except Exception as e:
            self.show_error_popup(
                error_title="Processing Error",
                error_message=f"An error occurred while processing invoices: {e}",
            )

    ###########################################################################
    ###               InvoiceAppDisplay -> show_error_popup()               ###
    ###########################################################################
    def show_error_popup(self, error_title: str, error_message: str):
        """
        Displays an error message in a popup window

        Args:
            error_title (str): The title of the error popup
            error_message (str): The error message to display
        """

        # If in integration test mode, do not show popups since this will be running
        # in a headless environment, and will halt testing
        if self.argument_provider.integration_test_mode:
            return

        messagebox.showerror(error_title, error_message)

    ###########################################################################
    ###                 InvoiceAppDisplay -> handle_clear()                 ###
    ###########################################################################
    def handle_clear(self):
        """
        Clears the output box and resets the selected file path
        """
        self.selected_file.set("")
        if self.output_box:
            self.output_box.delete(1.0, tk.END)

    ###########################################################################
    ###            InvoiceAppDisplay -> _open_config_editor()               ###
    ###########################################################################
    def _open_config_editor(self, config_path: Path, title: str):
        """
        Opens a native, editable window for the given config file, prefilled with
        its current contents and wired to persist edits via the save callback

        Args:
            config_path (Path): The config file to open for editing
            title (str): The title to display on the editor window
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
    ###               InvoiceAppDisplay -> _open_log_viewer()               ###
    ###########################################################################
    def _open_log_viewer(self, log_path: Path, title: str):
        """
        Opens a native, read-only window showing the given log file if it exists.
        Shows an error popup if the file has not been created yet.

        Args:
            log_path (Path): The log file to open for viewing
            title (str): The title to display on the viewer window
        """
        if log_path.exists():
            FileEditorWindow(
                parent=self,
                title=title,
                file_path=log_path,
                initial_text=self.read_file_callback(log_path),
                theme=self.current_theme,
                font_family=self.current_font_family,
                font_size=self.current_font_size,
                editable=False,
            )
        else:
            self.show_error_popup(
                error_title="File Not Found",
                error_message=f"Log not found at: {log_path}. Process an invoice to generate the log.",
            )

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_cost_criteria()             ###
    ###########################################################################
    def handle_cost_criteria(self):
        """
        Opens the Cost Criteria config file in a native editor window
        """
        self._open_config_editor(COST_CRITERIA_PATH, "Cost Criteria")

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_payment_terms()             ###
    ###########################################################################
    def handle_payment_terms(self):
        """
        Opens the Payment Terms config file in a native editor window
        """
        self._open_config_editor(PAYMENT_TERMS_PATH, "Payment Terms")

    ###########################################################################
    ###              InvoiceAppDisplay -> handle_sales_reps()               ###
    ###########################################################################
    def handle_sales_reps(self):
        """
        Opens the Sales Reps config file in a native editor window
        """
        self._open_config_editor(SALES_REPS_PATH, "Sales Reps")

    ###########################################################################
    ###              InvoiceAppDisplay -> handle_results_log()              ###
    ###########################################################################
    def handle_results_log(self):
        """
        Opens the results log file in a native read-only viewer window if it
        exists. Shows an error popup if the file has not been created yet.
        """
        self._open_log_viewer(RESULTS_LOG_PATH, "Results Log")

    ###########################################################################
    ###               InvoiceAppDisplay -> handle_debug_log()               ###
    ###########################################################################
    def handle_debug_log(self):
        """
        Opens the debug log file in a native read-only viewer window if it exists.
        Shows an error popup if the file has not been created yet.
        """
        self._open_log_viewer(DEBUG_LOG_PATH, "Debug Log")

    ###########################################################################
    ###                 InvoiceAppDisplay -> apply_theme()                  ###
    ###########################################################################
    def apply_theme(self, theme: Theme):
        """
        Applies a color theme to all widgets in the application

        Args:
            theme (Theme): The theme to apply
        """
        self.current_theme = theme

        self.configure(bg=theme.bg_main)
        self.title_label.configure(bg=theme.bg_main, fg=theme.label_fg)
        self.file_frame.configure(bg=theme.bg_main)
        self.file_entry.configure(
            bg=theme.bg_entry, fg=theme.bg_main, insertbackground=theme.fg_text
        )
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
        self.output_label.configure(bg=theme.bg_main, fg=theme.label_fg)
        self.output_box.configure(
            bg=theme.bg_entry, fg=theme.fg_text, insertbackground=theme.fg_text
        )

        # Persist the choice so it is restored on the next launch
        self.save_settings_callback(SETTING_KEY_THEME, theme.name)

    ###########################################################################
    ###              InvoiceAppDisplay -> apply_font_family()               ###
    ###########################################################################
    def apply_font_family(self, family: str):
        """
        Applies a font family to all text on screen

        Args:
            family (str): The font family to apply
        """
        self.current_font_family = family
        self._apply_font()

        # Persist the choice so it is restored on the next launch
        self.save_settings_callback(SETTING_KEY_FONT_FAMILY, family)

    ###########################################################################
    ###               InvoiceAppDisplay -> apply_font_size()                ###
    ###########################################################################
    def apply_font_size(self, size: int):
        """
        Applies a font size to all text on screen

        Args:
            size (int): The font size to apply
        """
        self.current_font_size = size
        self._apply_font()

        # Persist the choice so it is restored on the next launch. Settings are
        # stored as strings, so the size is converted on the way out.
        self.save_settings_callback(SETTING_KEY_FONT_SIZE, str(size))

    ###########################################################################
    ###               InvoiceAppDisplay -> _parse_font_size()               ###
    ###########################################################################
    def _parse_font_size(self, value) -> int:
        """
        Converts a persisted font size value into an int, falling back to the
        default when it is missing or not a valid integer.

        Args:
            value: The raw font size loaded from settings (a string, or None when
                no size has been persisted yet)

        Returns:
            int: The restored font size, or DEFAULT_FONT_SIZE if value is missing
                or non-numeric.
        """
        try:
            return int(value)
        except (TypeError, ValueError):
            return DEFAULT_FONT_SIZE

    ###########################################################################
    ###                 InvoiceAppDisplay -> _apply_font()                  ###
    ###########################################################################
    def _apply_font(self):
        """
        Applies the current font family and size to all text on screen
        """
        font = (self.current_font_family, self.current_font_size, "bold")
        self.title_label.configure(font=font)
        self.browse_button.configure(font=font)
        self.process_invoice_button.configure(font=font)
        self.exit_button.configure(font=font)
        self.process_all_invoices_button.configure(font=font)
        self.output_label.configure(font=font)
        self.output_box.configure(font=font)
