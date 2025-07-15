import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path

from .InvoiceAppFileIO import *
from .Invoice import *
from .color_theme import *


# Invoice App Display class to hold the GUI for selecting and processing invoices
# This implementation uses tkinter for the GUI
class InvoiceAppDisplay(tk.Tk):

    # __init__ Constructor, takes in a callback function as input
    # param: process_callback: function, a callback function to process the selected invoice file
    # param: title: str, the title of the application window
    # param: window_resolution: str, the resolution of the application window (e.g., "750x750")
    # param: invoices_dir: str, the directory where invoice PDFs are located
    # returns: Created InvoiceAppDisplay object
    def __init__(self, process_callback, title, window_resolution, invoices_dir):
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

    # build_widgets: Creates the GUI widgets for the application
    # This includes a title label, file selection entry, browse button, and action buttons
    # param: N/A
    # returns: N/A
    def build_widgets(self):

        # Define color scheme
        bg_main = DARK_GRAY
        bg_frame = DARKER_GRAY
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
        self.file_frame = tk.Frame(self, bg=bg_frame)
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

        # Create button for processing all invoices in the Invoices folder
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

        # Output box to display results
        self.output_label = tk.Label(
            self, text="Output:", font=("Segoe UI", 12, "bold"), bg=bg_main, fg=label_fg
        )
        self.output_label.pack(anchor="w", padx=22, pady=(0, 2))

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

    # handle_browse_button: On "Browse" button press, opens a file dialog to select a PDF invoice file. Once selected, the file is set
    # to the selected_file member variable
    # param: N/A
    # returns: N/A
    def handle_browse_button(self):

        # Open a file dialog to select a PDF invoice file
        file_path = filedialog.askopenfilename(
            initialdir=self.invoices_dir,
            title="Select Invoice PDF",
            filetypes=[("PDF files", "*.pdf")],  # Filter for PDF files only
        )

        # If a valid filepath was selected, update the selected_file variable
        if file_path:
            self.selected_file.set(file_path)

    # display_invoice_output: Displays the calculated totals of the invoice in the output box
    # param: invoice: Invoice object, the processed invoice containing calculated totals
    # param: append, bool: whether to append to the output box or clear it first before writing
    def display_invoice_output(self, invoice, append_output=False):

        # Clear the output box if not appending
        if not append_output:
            self.output_box.delete(1.0, tk.END)

        # If appending, insert a newline before adding the new output
        else:
            self.output_box.insert(tk.END, "\n")

        self.output_box.insert(tk.END, invoice.to_formatted_string())
        return

    # handle_process_invoice: On "Process This Invoice" button press, processes the selected PDF invoice file by forwarding
    # the call to the provided process_callback function specified during construction
    def handle_process_invoice(self):

        # Try to use the last selected file from the file dialogue widget
        file_path = self.selected_file.get()

        # If no file is selected, show an error popup and do nothing
        if not file_path:
            self.show_error_popup("No file selected", "Please select a PDF file first.")
            return

        # Forward the call to the process_callback function with the selected file path. Append output is false to reset the
        # output windows and results.txt file since this is the only invoice being processed
        self.process_callback(file_path, append_output=False)

        # TODO: Still need to either figure out the diff issue or add the popup in here
        # Diff should probably be handled in the controller

    # handle_process_all_invoices: On "Process This Invoice" button press, processes the selected PDF invoice file by forwarding
    # the call to the provided process_callback function specified during construction
    def handle_process_all_invoices(self):

        try:

            # Loop through all invoice files in the invoices directory and process each one
            for file_path in Path(self.invoices_dir).resolve().iterdir():

                # Process each invoice, appending output to the results.txt file and output widget
                self.process_callback(file_path, append_output=True)

        except Exception as e:
            self.show_error_popup(
                "Processing Error", f"An error occurred while processing invoices: {e}"
            )

    # show_error_popup: Displays an error message in a popup window
    # param: error_title: str, the title of the error popup
    # param: error_message: str, the error message to display
    def show_error_popup(self, error_title, error_message):
        messagebox.showerror(error_title, error_message)
