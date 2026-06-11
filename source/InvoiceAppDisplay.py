import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

from source.Invoice import Invoice
from source.ArgumentProvider import ArgumentProvider
from source.color_theme import (
    ALL_THEMES,
    BLUE,
    DARK,
    DARK_GRAY,
    IVORY,
    LIGHT_BLUE,
    MEDIUM_GRAY,
    RED,
    Theme,
)
from source.font_settings import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    FONT_FAMILIES,
    FONT_SIZES,
)
from source.platform_utils import open_in_system_editor

# Future TODO: Add second output window for errors, instead of cluttering the screen with
#              pop up windows when Fishbowl invoices present rounding errors
# Future TODO: Make abstract GUI class and try and use other frameworks? PyQT could be cool


# Invoice App Display class to own the GUI for selecting and processing invoices
# This implementation uses tkinter for the GUI
class InvoiceAppDisplay(tk.Tk):

    ###########################################################################
    ###                   InvoiceAppDisplay -> __init__()                   ###
    ###########################################################################
    def __init__(
        self,
        process_callback,
        title: str,
        window_resolution: str,
        invoices_dir: str,
        payment_terms_path: str,
        sales_reps_path: str,
        cost_criteria_path: str,
        results_log_path: str,
        debug_log_path: str,
    ):
        """
        Initializes the InvoiceAppDisplay object

        Args:
            process_callback (callable): Callback function to process the selected invoice file
            title (str): Title of the application window
            window_resolution (str): Resolution of the application window (e.g., "750x750")
            invoices_dir (str): Directory where invoice PDFs are located
            payment_terms_path (str): Path to the payment terms config file
            sales_reps_path (str): Path to the sales representatives config file
            cost_criteria_path (str): Path to the cost criteria config file
            results_log_path (str): Path to the results log file
            debug_log_path (str): Path to the debug log file (not present in the release configuration)
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

        # The filepath to expect invoice PDFs to be located
        self.invoices_dir = invoices_dir

        # The filepath to the config files
        self.payment_terms_path = payment_terms_path
        self.sales_reps_path = sales_reps_path
        self.cost_criteria_path = cost_criteria_path

        # The filepath to the log files
        self.results_log_path = results_log_path
        self.debug_log_path = debug_log_path

        # Active theme, defaults to Dark
        self.current_theme = DARK

        # Active font family, defaults to DEFAULT_FONT_FAMILY
        self.current_font_family = DEFAULT_FONT_FAMILY

        # Active font size, defaults to DEFAULT_FONT_SIZE
        self.current_font_size = DEFAULT_FONT_SIZE

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

        # Define color scheme
        bg_main = DARK_GRAY
        bg_entry = MEDIUM_GRAY
        fg_text = IVORY
        accent_blue = LIGHT_BLUE
        button_bg = BLUE
        button_fg = IVORY
        label_fg = BLUE

        self.configure(bg=bg_main)

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
        for theme in ALL_THEMES:
            theme_menu.add_command(
                label=theme.name,
                command=lambda t=theme: self.apply_theme(t),
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
            bg=bg_main,
            fg=label_fg,
        )
        self.title_label.pack(pady=(20, 10))

        # File selection frame
        self.file_frame = tk.Frame(self, bg=bg_main)
        self.file_frame.pack(padx=20, fill="x")

        self.file_entry = tk.Entry(
            self.file_frame,
            textvariable=self.selected_file,
            state="readonly",
            width=50,
            bg=bg_entry,
            fg=bg_main,
            insertbackground=fg_text,
            relief="flat",
        )
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 5), pady=8)

        # Browse button to open file dialog
        self.browse_button = tk.Button(
            self.file_frame,
            text="Browse",
            command=self.handle_browse_button,
            bg=button_bg,
            fg=button_fg,
            activebackground=accent_blue,
            activeforeground=fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.browse_button.pack(side="left", padx=(10, 0), pady=8)

        # Action buttons frame
        self.button_frame = tk.Frame(self, bg=bg_main)
        self.button_frame.pack(pady=20)

        # Create button for processing a single invoice
        self.process_invoice_button = tk.Button(
            self.button_frame,
            text="Process This Invoice",
            command=self.handle_process_invoice,
            bg=button_bg,
            fg=button_fg,
            activebackground=accent_blue,
            activeforeground=fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.process_invoice_button.grid(row=0, column=0, padx=10)

        # Create button for exiting the application
        self.exit_button = tk.Button(
            self.button_frame,
            text="Exit",
            command=self.quit,
            bg=bg_entry,
            fg=fg_text,
            activebackground=RED,
            activeforeground=fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.exit_button.grid(row=0, column=1, padx=10)

        # Create button for processing all invoices in the Invoices folder at once
        self.process_all_invoices_button = tk.Button(
            self.button_frame,
            text="Process All Invoices",
            command=self.handle_process_all_invoices,
            bg=button_bg,
            fg=button_fg,
            activebackground=accent_blue,
            activeforeground=fg_text,
            relief="flat",
            font=(self.current_font_family, self.current_font_size, "bold"),
        )
        self.process_all_invoices_button.grid(row=0, column=2, padx=10)

        # Output Label before text results
        self.output_label = tk.Label(
            self,
            text="Output:",
            font=(self.current_font_family, self.current_font_size, "bold"),
            bg=bg_main,
            fg=label_fg,
        )
        self.output_label.pack(anchor="w", padx=22, pady=(0, 2))

        # Output box to display invoice results
        self.output_box = scrolledtext.ScrolledText(
            self,
            height=8,
            wrap="word",
            font=(self.current_font_family, self.current_font_size, "bold"),
            bg=bg_entry,
            fg=fg_text,
            insertbackground=fg_text,
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

        # Open a file dialog to select a PDF invoice file
        file_path = filedialog.askopenfilename(
            initialdir=self.invoices_dir,
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

        # Forward the call to the process_callback function with the selected file path. Append output is false to reset the
        # output windows and results.txt file since this is the only invoice being processed
        self.process_callback(file_path, append_output=False)

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
            for file_path in Path(self.invoices_dir).resolve().iterdir():

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
    ###             InvoiceAppDisplay -> handle_cost_criteria()             ###
    ###########################################################################
    def handle_cost_criteria(self):
        """
        Opens the Cost Criteria config file in the system default text editor
        """
        open_in_system_editor(self.cost_criteria_path)

    ###########################################################################
    ###             InvoiceAppDisplay -> handle_payment_terms()             ###
    ###########################################################################
    def handle_payment_terms(self):
        """
        Opens the Payment Terms config file in the system default text editor
        """
        open_in_system_editor(self.payment_terms_path)

    ###########################################################################
    ###              InvoiceAppDisplay -> handle_sales_reps()               ###
    ###########################################################################
    def handle_sales_reps(self):
        """
        Opens the Sales Reps config file in the system default text editor
        """
        open_in_system_editor(self.sales_reps_path)

    ###########################################################################
    ###              InvoiceAppDisplay -> handle_results_log()              ###
    ###########################################################################
    def handle_results_log(self):
        """
        Opens the results log file in the system default text editor if it exists.
        Shows an error popup if the file has not been created yet.
        """
        if Path(self.results_log_path).exists():
            open_in_system_editor(self.results_log_path)
        else:
            self.show_error_popup(
                error_title="File Not Found",
                error_message=f"Results log not found at: {self.results_log_path}",
            )

    ###########################################################################
    ###               InvoiceAppDisplay -> handle_debug_log()               ###
    ###########################################################################
    def handle_debug_log(self):
        """
        Opens the debug log file in the system default text editor if it exists.
        Shows an error popup if the file has not been created yet.
        """
        if Path(self.debug_log_path).exists():
            open_in_system_editor(self.debug_log_path)
        else:
            self.show_error_popup(
                error_title="File Not Found",
                error_message=f"Debug log not found at: {self.debug_log_path}",
            )

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
