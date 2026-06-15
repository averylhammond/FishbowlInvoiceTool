import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import Callable

from source.color_theme import Theme


# InvoiceDiscoveryWindow class to let the user copy downloaded invoice PDFs into
# the application's Invoices/ folder without leaving the app. The user browses to
# wherever invoices were downloaded, selects one or more PDFs, copies them in, and
# can repeat as many times as needed before closing. A running status area shows
# the outcome of each copy so the workflow needs no other window than ours.
class InvoiceDiscoveryWindow(tk.Toplevel):

    ###########################################################################
    ###                 InvoiceDiscoveryWindow -> __init__()                ###
    ###########################################################################
    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        theme: Theme,
        font_family: str,
        font_size: int,
        copy_callback: Callable[[Path, bool], str],
    ):
        """
        Initializes the InvoiceDiscoveryWindow object

        Args:
            parent (tk.Misc): The parent window this window is attached to
            title (str): Title of the discovery window
            theme (Theme): The color theme to style the window with, snapshotted
                at open time
            font_family (str): The font family to display the text with
            font_size (int): The font size to display the text with
            copy_callback (Callable[[Path, bool], str]): Called with a source PDF
                path and an overwrite flag to copy the file into the Invoices/
                folder. Returns "copied", "exists", or "error" so this window can
                confirm overwrites and report each outcome to the user
        """

        super().__init__(parent)

        # Callback used to copy a selected invoice into the Invoices/ folder
        self.copy_callback = copy_callback

        # Snapshot the active theme/font at open time so the window is styled
        # consistently with the rest of the application
        self.theme = theme
        self.font_family = font_family
        self.font_size = font_size

        # Source paths the user has selected and not yet copied. Browsing again
        # adds to this list so the user can gather invoices from several folders
        # before copying them all in at once.
        self.pending_files: list[Path] = []

        # Tkinter Widgets
        # fmt:off
        self.instruction_label: tk.Label                   | None = None
        self.selection_var:     tk.StringVar               | None = None
        self.selection_entry:   tk.Entry                   | None = None
        self.button_frame:      tk.Frame                   | None = None
        self.browse_button:     tk.Button                  | None = None
        self.copy_button:       tk.Button                  | None = None
        self.close_button:      tk.Button                  | None = None
        self.status_box:        scrolledtext.ScrolledText  | None = None
        # fmt:on

        self.title(title)
        self.configure(bg=theme.bg_main)

        self.build_widgets()

    ###########################################################################
    ###              InvoiceDiscoveryWindow -> build_widgets()              ###
    ###########################################################################
    def build_widgets(self):
        """
        Creates the instruction label, selection display, action buttons
        (Browse / Copy Invoice(s) / Close), and the read-only status area
        """

        # Instruction label explaining the workflow
        self.instruction_label = tk.Label(
            self,
            text="Browse to your downloaded invoices, then copy them into the Invoices/ folder.",
            font=(self.font_family, self.font_size, "bold"),
            bg=self.theme.bg_main,
            fg=self.theme.label_fg,
        )
        self.instruction_label.pack(padx=20, pady=(20, 10))

        # Read-only entry showing the currently selected (pending) files
        self.selection_var = tk.StringVar()
        self.selection_entry = tk.Entry(
            self,
            textvariable=self.selection_var,
            state="readonly",
            bg=self.theme.bg_entry,
            fg=self.theme.bg_main,
            insertbackground=self.theme.fg_text,
            relief="flat",
        )
        self.selection_entry.pack(padx=20, pady=(0, 10), fill="x")

        # Frame holding the action buttons
        self.button_frame = tk.Frame(self, bg=self.theme.bg_main)
        self.button_frame.pack(pady=(0, 10))

        # Browse button to select one or more invoice PDFs to copy in
        self.browse_button = tk.Button(
            self.button_frame,
            text="Browse",
            command=self.handle_browse,
            bg=self.theme.button_bg,
            fg=self.theme.button_fg,
            activebackground=self.theme.accent,
            activeforeground=self.theme.fg_text,
            relief="flat",
            font=(self.font_family, self.font_size, "bold"),
        )
        self.browse_button.grid(row=0, column=0, padx=10)

        # Copy button to copy all selected invoices into the Invoices/ folder
        self.copy_button = tk.Button(
            self.button_frame,
            text="Copy Invoice(s)",
            command=self.handle_copy,
            bg=self.theme.button_bg,
            fg=self.theme.button_fg,
            activebackground=self.theme.accent,
            activeforeground=self.theme.fg_text,
            relief="flat",
            font=(self.font_family, self.font_size, "bold"),
        )
        self.copy_button.grid(row=0, column=1, padx=10)

        # Close button to dismiss the window when discovery is finished
        self.close_button = tk.Button(
            self.button_frame,
            text="Close",
            command=self.destroy,
            bg=self.theme.button_bg,
            fg=self.theme.button_fg,
            activebackground=self.theme.accent,
            activeforeground=self.theme.fg_text,
            relief="flat",
            font=(self.font_family, self.font_size, "bold"),
        )
        self.close_button.grid(row=0, column=2, padx=10)

        # Read-only status area reporting the outcome of each copy so the user
        # gets feedback without leaving the window
        self.status_box = scrolledtext.ScrolledText(
            self,
            height=8,
            wrap="word",
            font=(self.font_family, self.font_size, "bold"),
            bg=self.theme.bg_entry,
            fg=self.theme.fg_text,
            insertbackground=self.theme.fg_text,
            relief="flat",
        )
        self.status_box.configure(state="disabled")
        self.status_box.pack(padx=20, pady=(0, 20), fill="both", expand=True)

    ###########################################################################
    ###             InvoiceDiscoveryWindow -> _default_browse_dir()         ###
    ###########################################################################
    def _default_browse_dir(self) -> str:
        """
        Determines the folder the Browse dialog should open in by default.

        Returns:
            str: The user's Downloads folder if it exists (where invoices are
                most likely downloaded), otherwise the user's home folder.
        """
        downloads = Path.home() / "Downloads"
        return str(downloads if downloads.exists() else Path.home())

    ###########################################################################
    ###                InvoiceDiscoveryWindow -> handle_browse()            ###
    ###########################################################################
    def handle_browse(self):
        """
        On "Browse" press, opens a multi-select file dialog for PDF invoices and
        adds the chosen files to the pending list. Browsing again appends to the
        selection so invoices can be gathered from several folders before copying.
        """

        # askopenfilenames (plural) returns a tuple of selected paths, allowing
        # the user to pick several invoices at once
        selected = filedialog.askopenfilenames(
            initialdir=self._default_browse_dir(),
            title="Select Invoice PDFs",
            filetypes=[("PDF files", "*.pdf")],
        )

        # If the user cancelled, leave the current selection untouched
        if not selected:
            return

        # Append the newly selected files to the pending list
        for file_path in selected:
            self.pending_files.append(Path(file_path))

        # Update the selection display to reflect the pending files
        self.selection_var.set(
            ", ".join(path.name for path in self.pending_files)
        )

    ###########################################################################
    ###                 InvoiceDiscoveryWindow -> handle_copy()             ###
    ###########################################################################
    def handle_copy(self):
        """
        On "Copy Invoice(s)" press, copies each pending invoice into the
        Invoices/ folder. If a same-named file already exists, asks the user to
        confirm an overwrite before replacing it. Reports the outcome of each
        file in the status area, then clears the pending selection.
        """

        # Nothing to do if the user has not selected any files yet
        if not self.pending_files:
            self._append_status("No files selected. Use Browse to select invoices.")
            return

        for source_path in self.pending_files:

            # Attempt the copy without overwriting first
            result = self.copy_callback(source_path, False)

            # If a same-named file already exists, confirm before overwriting
            if result == "exists":
                overwrite = messagebox.askyesno(
                    "File Exists",
                    f"{source_path.name} already exists in the Invoices/ folder. Overwrite it?",
                )
                if overwrite:
                    result = self.copy_callback(source_path, True)
                else:
                    self._append_status(f"Skipped {source_path.name} (already exists).")
                    continue

            # Report the outcome of the copy
            if result == "copied":
                self._append_status(f"Copied {source_path.name}.")
            elif result == "error":
                self._append_status(f"Failed to copy {source_path.name}.")

        # Clear the pending selection now that it has been processed
        self.pending_files.clear()
        self.selection_var.set("")

    ###########################################################################
    ###               InvoiceDiscoveryWindow -> _append_status()            ###
    ###########################################################################
    def _append_status(self, message: str):
        """
        Appends a status line to the read-only status box, scrolling to show it.

        Args:
            message (str): The status message to append
        """

        # The status box is read-only, so temporarily enable it to write
        self.status_box.configure(state="normal")
        self.status_box.insert(tk.END, message + "\n")
        self.status_box.see(tk.END)
        self.status_box.configure(state="disabled")
