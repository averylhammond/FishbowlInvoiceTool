import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

from source.InvoiceAppFileIO import *
from source.Invoice import *
from source.color_theme import *

# FUTURE TODO: Implement a dynamic theme that can be changed at runtime through user input
# Future TODO: Let the config text files be controlled through tabs on the GUI, store results
#              in database somewhere so the txt files don't need to be retained
# Future TODO: Add second output window for errors, instead of cluttering the screen with
#              pop up windows when Fishbowl invoices present rounding errors


# Invoice App Display class to hold the GUI for selecting and processing invoices
# This implementation uses tkinter for the GUI
class InvoiceAppDisplay(tk.Tk):

    def __init__(
        self,
        process_callback,
        title: str,
        window_resolution: str,
        invoices_dir: str,
    ):
        """
        Initializes the InvoiceAppDisplay object

        Args:
            process_callback (callable): Callback function to process the selected invoice file
            title (str): Title of the application window
            window_resolution (str): Resolution of the application window (e.g., "750x750")
            invoices_dir (str): Directory where invoice PDFs are located
        """

        super().__init__()

        # Title applied to the application window
        self.title(title)

        # Resolution of the application window
        self.geometry(window_resolution)

        # Whether the user can resize the window
        self.resizable(False, False)

        # Holds the last selected invoice filepath
        self.selected_file = tk.StringVar()

        # Callback function to process the selected invoice file
        self.process_callback = process_callback

        # The filepath to expect invoice PDFs to be located
        self.invoices_dir = invoices_dir

        # Tkinter Widgets
        # fmt:off
        self.title_label                 = None
        self.file_frame                  = None
        self.file_entry                  = None
        self.browse_button               = None
        self.button_frame                = None
        self.process_invoice_button      = None
        self.exit_button                 = None
        self.process_all_invoices_button = None
        self.output_label                = None
        self.output_box                  = None
        # fmt:on

        self.build_widgets()

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

        # Title Label
        self.title_label = tk.Label(
            self,
            text="Choose a Fishbowl Invoice PDF to Process",
            font=("Segoe UI", 16, "bold"),
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
            font=("Segoe UI", 10, "bold"),
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
            font=("Segoe UI", 10, "bold"),
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
            font=("Segoe UI", 10, "bold"),
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
            font=("Segoe UI", 10, "bold"),
        )
        self.process_all_invoices_button.grid(row=0, column=2, padx=10)

        # Output Label before text results
        self.output_label = tk.Label(
            self,
            text="Output:",
            font=("Segoe UI", 12, "bold"),
            bg=bg_main,
            fg=label_fg,
        )
        self.output_label.pack(anchor="w", padx=22, pady=(0, 2))

        # Output box to display invoice results
        self.output_box = scrolledtext.ScrolledText(
            self,
            height=8,
            wrap="word",
            font=("Segoe UI", 15, "bold"),
            bg=bg_entry,
            fg=fg_text,
            insertbackground=fg_text,
            relief="flat",
        )
        self.output_box.pack(padx=20, pady=(0, 10), fill="both", expand=True)

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

    def show_error_popup(self, error_title: str, error_message: str):
        """
        Displays an error message in a popup window

        Args:
            error_title (str): The title of the error popup
            error_message (str): The error message to display
        """

        messagebox.showerror(error_title, error_message)
