from decimal import Decimal
from pathlib import Path

DECIMAL_ZERO = Decimal("0.00")

# Display name of this application. Passed to the shared AboutWindow, which is
# application-agnostic and takes the name it shows by injection.
APP_NAME = "Fishbowl Invoice Tool"

# Current application version. Single source of truth for the version, kept
# consistent with application releases and surfaced to the user via Help -> About.
VERSION = "4.0.2"

# GitHub repository ("owner/name") this app releases from. Passed to the shared
# UpdateCoordinator so it knows which repo's releases to compare VERSION against.
GITHUB_REPO = "averylhammond/FishbowlInvoiceTool"

# Name of the installer asset published on each GitHub release, matched against the
# release's assets by the shared UpdateCoordinator to find the file an in-app update
# downloads and runs. Injected rather than hardcoded upstream because each Fishbowl
# app names its own installer; a release without a matching asset simply offers the
# manual download instead. Must stay in step with installer.iss's OutputBaseFilename.
INSTALLER_ASSET_PATTERN = "FishbowlInvoiceTool_Setup.exe"

# Application file paths, relative to the executable's current working directory.

# Base directories. The specific file paths below are composed from these.
LOGS_DIR = Path("logs")
CONFIGS_DIR = Path("Configs")
INVOICES_PATH = Path("Invoices")
DATA_DIR = Path("data")

# Log files
DEBUG_LOG_PATH = LOGS_DIR / "debug.txt"
RESULTS_LOG_PATH = LOGS_DIR / "results.txt"

# Config files
PAYMENT_TERMS_PATH = CONFIGS_DIR / "Payment_Terms.txt"
SALES_REPS_PATH = CONFIGS_DIR / "Sales_Reps.txt"
COST_CRITERIA_PATH = CONFIGS_DIR / "Cost_Criteria.txt"

# Database file holding persisted user settings (theme, font, etc.)
SETTINGS_DB_PATH = DATA_DIR / "settings.db"

# User guide shipped next to the executable; surfaced in-app via Help -> Open User Guide.
USER_GUIDE_PATH = Path("USER_GUIDE.txt")

# Keys under which user settings are persisted in the settings database. Shared
# between the display (which reads/writes them) and any other consumer so the
# two never drift apart.
SETTING_KEY_THEME = "theme"
SETTING_KEY_FONT_FAMILY = "font_family"
SETTING_KEY_FONT_SIZE = "font_size"
