import os
import sys
import subprocess
from pathlib import Path


# TODO: Can probably get rid of this file once I have added tkinter windows to open up, display
#       and save files so I don't need to rely on the system text editor
def open_in_system_editor(filepath: str):
    # Opens a file in the OS default text editor using the absolute path to the file
    path = Path(filepath)
    if not path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        path = project_root / path

    # Windows
    if sys.platform == "win32":
        os.startfile(path)
    # macOS
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    # Linux and other Unix-like systems
    else:
        subprocess.Popen(["xdg-open", str(path)])
