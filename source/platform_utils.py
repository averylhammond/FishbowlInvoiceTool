import os
import sys
import subprocess


def open_in_system_editor(filepath: str):
    """Opens a file in the OS default text editor."""
    if sys.platform == "win32":
        os.startfile(filepath)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", filepath])
    else:
        subprocess.Popen(["xdg-open", filepath])
