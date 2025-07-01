import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path


# Invoice App GUI class to hold the GUI for selecting and processing invoices
# This implementation uses tkinter for the GUI
class InvoiceAppGUI(tk.Tk):

    # __init__ Constructor, takes in a callback function as input
    # params: process_callback: function, a callback function to process the selected invoice file
    # returns: N/A
    def __init__(self, process_callback):
        super().__init__()

        self.title("Invoice Processor")
        self.geometry("750x300")
        self.resizable(False, False)

        self.selected_file = tk.StringVar()
        self.process_callback = process_callback

        self.build_widgets()

    # build_widgets: Creates the GUI widgets for the application
    # This includes a title label, file selection entry, browse button, and action buttons
    # params: N/A
    # returns: N/A
    def build_widgets(self):

        # Title Label
        title_label = tk.Label(
            self, text="Choose a Fishbowl Invoice PDF to Process", font=("Segoe UI", 14)
        )
        title_label.pack(pady=(20, 10))

        # File selection frame
        file_frame = tk.Frame(self)
        file_frame.pack(padx=20, fill="x")

        file_entry = tk.Entry(
            file_frame, textvariable=self.selected_file, state="readonly", width=50
        )
        file_entry.pack(side="left", fill="x", expand=True)

        # Browse button to open file dialog
        browse_button = tk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_button.pack(side="left", padx=(10, 0))

        # Action buttons frame
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        # Create button for processing a single invoice
        process_button = tk.Button(
            button_frame, text="Process This Invoice", command=self.process_file
        )
        process_button.grid(row=0, column=0, padx=10)

        # Create button for exiting the application
        exit_button = tk.Button(button_frame, text="Exit", command=self.quit)
        exit_button.grid(row=0, column=1, padx=10)

    # browse_file: On "Browse" button press, opens a file dialog to select a PDF invoice file. Once selected, the file is set
    # to the selected_file member variable
    # params: N/A
    # returns: N/A
    def browse_file(self):
        initial_dir = Path("./Invoices").resolve()
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="Select Invoice PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if file_path:
            self.selected_file.set(file_path)

    # process_file: On "Process This Invoice" button press, processes the selected PDF invoice file by forwarding
    # the call to the provided process_callback function specified during construction
    # params: N/A
    # returns: N/A
    # note: If no file is selected, a warning message is shown
    def process_file(self):
        file_path = self.selected_file.get()
        if not file_path:
            messagebox.showwarning(
                "No file selected", "Please select a PDF file first."
            )
            return

        try:
            self.process_callback(file_path)
            messagebox.showinfo("Success", "Invoice processed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
