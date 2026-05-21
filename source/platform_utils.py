import os
import sys
import subprocess


# TODO: Can probably get rid of this file once I have added tkinter windows to open up, display
#       and save files so I don't need to rely on the system text editor
def open_in_system_editor(filepath: str):
    """Opens a file in the OS default text editor."""
    if sys.platform == "win32":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])
