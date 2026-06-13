import tkinter as tk
from tkinter import scrolledtext
from pathlib import Path
from typing import Callable

from source.color_theme import Theme
from source.font_settings import MONOSPACE_FONT_FAMILY


# FileEditorWindow class to view or edit a single text file natively within the
# application. The same window serves both editable config files (with a Save
# button) and read-only log files (no Save button, editing disabled) via the
# editable flag.
class FileEditorWindow(tk.Toplevel):

    ###########################################################################
    ###                   FileEditorWindow -> __init__()                    ###
    ###########################################################################
    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        file_path: Path,
        initial_text: str,
        theme: Theme,
        font_family: str,
        font_size: int,
        editable: bool = True,
        save_callback: Callable[[Path, str], None] | None = None,
    ):
        """
        Initializes the FileEditorWindow object

        Args:
            parent (tk.Misc): The parent window this window is attached to
            title (str): Title of the editor window
            file_path (Path): The file path this window is viewing/editing, passed
                back to the save_callback when the user saves
            initial_text (str): The current file contents to display
            theme (Theme): The color theme to style the window with, snapshotted at
                open time
            font_family (str): The font family to display the text with
            font_size (int): The font size to display the text with
            editable (bool): Whether the contents can be edited and saved. When
                False, the text is read-only and no Save button is shown
                (used for viewing log files). Defaults to True
            save_callback (Callable[[Path, str], None] | None): Called with the
                file path and the edited contents when the user saves. Required
                when editable is True; ignored when editable is False
        """

        super().__init__(parent)

        # File this window is bound to; passed back to the save callback on save
        self.file_path = file_path

        # Whether the contents can be edited and saved
        self.editable = editable

        # Callback used to persist edits when the user saves
        self.save_callback = save_callback

        # Snapshot the active theme/font at open time so the window is styled
        # consistently with the rest of the application
        self.theme = theme
        self.font_family = font_family
        self.font_size = font_size

        # Tkinter Widgets
        # fmt:off
        self.text_box:     scrolledtext.ScrolledText | None = None
        self.button_frame: tk.Frame                  | None = None
        self.save_button:  tk.Button                 | None = None
        self.close_button: tk.Button                 | None = None
        # fmt:on

        self.title(title)
        self.configure(bg=theme.bg_main)

        self.build_widgets(initial_text)

    ###########################################################################
    ###                 FileEditorWindow -> build_widgets()                 ###
    ###########################################################################
    def build_widgets(self, initial_text: str):
        """
        Creates the text box and action buttons (Save when editable, plus Close)
        for the window

        Args:
            initial_text (str): The current file contents to display in the text box
        """

        # Text box displaying the file contents. A fixed-width font is used (rather
        # than the application's display font) so the asterisk borders and columns
        # in the config files stay aligned, the way they appear in a text editor.
        # TODO: Remove use of MONOSPACE once the format of the config files can be
        #       changed, and the commment header in the file does not cause alignment issues
        self.text_box = scrolledtext.ScrolledText(
            self,
            wrap="word",
            font=(MONOSPACE_FONT_FAMILY, self.font_size, "bold"),
            bg=self.theme.bg_entry,
            fg=self.theme.fg_text,
            insertbackground=self.theme.fg_text,
            relief="flat",
        )
        self.text_box.insert(tk.END, initial_text)
        self.text_box.pack(padx=20, pady=(20, 10), fill="both", expand=True)

        # Frame holding the action buttons along the bottom of the window
        self.button_frame = tk.Frame(self, bg=self.theme.bg_main)
        self.button_frame.pack(pady=(0, 20))

        # When editable, offer a Save button that persists the edits. When not
        # editable (log viewing), disable editing and show no Save button (the
        # Close button then sits where the Save button would have been).
        if self.editable:
            self.save_button = tk.Button(
                self.button_frame,
                text="Save",
                command=self.handle_save,
                bg=self.theme.button_bg,
                fg=self.theme.button_fg,
                activebackground=self.theme.accent,
                activeforeground=self.theme.fg_text,
                relief="flat",
                font=(self.font_family, self.font_size, "bold"),
            )
            self.save_button.grid(row=0, column=0, padx=10)
        else:
            self.text_box.configure(state="disabled")

        # Close button to dismiss the window; placed next to Save when present,
        # otherwise in the first column where Save would have been
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
        self.close_button.grid(row=0, column=1 if self.editable else 0, padx=10)

    ###########################################################################
    ###                  FileEditorWindow -> handle_save()                  ###
    ###########################################################################
    def handle_save(self):
        """
        Reads the current contents of the text box and forwards them, along with
        the bound file path, to the save_callback so the file is persisted
        """

        # Grab everything in the text box (tkinter appends a trailing newline that
        # is stripped so repeated saves do not accumulate blank lines)
        contents = self.text_box.get("1.0", tk.END)
        if contents.endswith("\n"):
            contents = contents[:-1]

        if self.save_callback:
            self.save_callback(self.file_path, contents)
