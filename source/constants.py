from decimal import Decimal
from pathlib import Path

DECIMAL_ZERO = Decimal("0.00")

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

# Keys under which user settings are persisted in the settings database. Shared
# between the display (which reads/writes them) and any other consumer so the
# two never drift apart.
SETTING_KEY_THEME = "theme"
SETTING_KEY_FONT_FAMILY = "font_family"
SETTING_KEY_FONT_SIZE = "font_size"
