from decimal import Decimal
from pathlib import Path

DECIMAL_ZERO = Decimal("0.00")

# Application file paths, relative to the executable's current working directory.

# Base directories. The specific file paths below are composed from these.
LOGS_DIR = Path("logs")
CONFIGS_DIR = Path("Configs")
INVOICES_PATH = Path("Invoices")

# Log files
DEBUG_LOG_PATH = LOGS_DIR / "debug.txt"
RESULTS_LOG_PATH = LOGS_DIR / "results.txt"

# Config files
PAYMENT_TERMS_PATH = CONFIGS_DIR / "Payment_Terms.txt"
SALES_REPS_PATH = CONFIGS_DIR / "Sales_Reps.txt"
COST_CRITERIA_PATH = CONFIGS_DIR / "Cost_Criteria.txt"
