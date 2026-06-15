# This file contains font definitions and font size options for the application.

# Default font family applied on startup
DEFAULT_FONT_FAMILY = "Segoe UI"

# Selectable font families, chosen from the most popular fonts
FONT_FAMILIES = [
    "Arial",
    "Helvetica",
    "Times New Roman",
    "Calibri",
    "Segoe UI",
    "Verdana",
    "Georgia",
    "Cambria",
    "Courier New",
    "Tahoma",
]

# Fixed-width font used where character alignment matters (e.g. the file editor),
# so the asterisk borders and columns in the config files line up the same way
# they do in a plain-text editor regardless of the application's display font
# TODO: Remove use of MONOSPACE once the format of the config files can be
#       changed, and the commment header in the file does not cause alignment issues
MONOSPACE_FONT_FAMILY = "Courier New"

# Default font size applied on startup
DEFAULT_FONT_SIZE = 12

# Selectable font sizes, from 6 to 32 in increments of 2
FONT_SIZES = list(range(6, 33, 2))
