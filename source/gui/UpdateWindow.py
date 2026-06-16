import tkinter as tk
import webbrowser

from source.gui.color_theme import Theme
from source.gui.ThemedSubwindow import ThemedSubwindow


# UpdateWindow class to notify the user that a newer release is available. It is a
# small window showing the available version alongside a Download button that opens
# the release's GitHub page in the user's browser, plus a Close button to dismiss
# it. Like the other themed subwindows it snapshots the active theme/font at open
# time and centers itself over the main application window (both handled by
# ThemedSubwindow).
class UpdateWindow(ThemedSubwindow):

    ###########################################################################
    ###                     UpdateWindow -> __init__()                     ###
    ###########################################################################
    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        latest_version: str,
        release_url: str,
        theme: Theme,
        font_family: str,
        font_size: int,
    ):
        """
        Initializes the UpdateWindow object

        Args:
            parent (tk.Misc): The parent window this window is attached to
            title (str): Title of the update window
            latest_version (str): The newer release's version to display
            release_url (str): The URL of the release's page on GitHub, opened when
                the Download button is pressed
            theme (Theme): The color theme to style the window with, snapshotted
                at open time
            font_family (str): The font family to display the text with
            font_size (int): The font size to display the text with
        """

        super().__init__(parent, title, theme, font_family, font_size)

        # The newer release's version and the page to send the user to
        self.latest_version = latest_version
        self.release_url = release_url

        # Tkinter Widgets
        # fmt:off
        self.info_label:      tk.Label  | None = None
        self.download_button: tk.Button | None = None
        self.close_button:    tk.Button | None = None
        # fmt:on

        self.build_widgets()

        # Position the window over the main application window rather than letting
        # it default to the top-left corner of the screen
        self._center_over_parent()

    ###########################################################################
    ###                   UpdateWindow -> build_widgets()                  ###
    ###########################################################################
    def build_widgets(self):
        """
        Creates the label announcing the available version, the Download button
        that opens the release page, and the Close button used to dismiss the
        window
        """

        # Label announcing that a newer release is available
        self.info_label = tk.Label(
            self,
            text=f"Version {self.latest_version} is available",
            font=(self.font_family, self.font_size, "bold"),
            bg=self.theme.bg_main,
            fg=self.theme.label_fg,
        )
        self.info_label.pack(padx=20, pady=(20, 10))

        # Download button to open the release page in the user's browser
        self.download_button = tk.Button(
            self,
            text="Download",
            command=self._open_release_page,
            bg=self.theme.button_bg,
            fg=self.theme.button_fg,
            activebackground=self.theme.accent,
            activeforeground=self.theme.fg_text,
            relief="flat",
            font=(self.font_family, self.font_size, "bold"),
        )
        self.download_button.pack(pady=(0, 10))

        # Close button to dismiss the window
        self.close_button = tk.Button(
            self,
            text="Close",
            command=self.destroy,
            bg=self.theme.button_bg,
            fg=self.theme.button_fg,
            activebackground=self.theme.accent,
            activeforeground=self.theme.fg_text,
            relief="flat",
            font=(self.font_family, self.font_size, "bold"),
        )
        self.close_button.pack(pady=(0, 20))

    ###########################################################################
    ###                 UpdateWindow -> _open_release_page()               ###
    ###########################################################################
    def _open_release_page(self):
        """
        Opens the release's GitHub page in the user's default browser so they can
        download the newer version. The window stays open so the user can return
        to it; Close dismisses it.
        """

        webbrowser.open(self.release_url)
