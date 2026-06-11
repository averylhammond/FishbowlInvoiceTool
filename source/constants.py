from decimal import Decimal

# Shared constants used across the application. Defined once here and imported
# wherever needed so values like DECIMAL_ZERO are never redefined per-module.

DECIMAL_ZERO = Decimal("0.00")

# Application file paths, relative to the executable's current working directory.
# Defined once here so they are not redefined as literals throughout the codebase.

# Base directories. The specific file paths below are composed from these, so
# relocating the logs or configs only requires changing the directory here.
LOGS_DIR = "logs"
CONFIGS_DIR = "Configs"
INVOICES_PATH = "Invoices"

# Log files
DEBUG_LOG_PATH = f"{LOGS_DIR}/debug.txt"
RESULTS_LOG_PATH = f"{LOGS_DIR}/results.txt"

# Config files
PAYMENT_TERMS_PATH = f"{CONFIGS_DIR}/Payment_Terms.txt"
SALES_REPS_PATH = f"{CONFIGS_DIR}/Sales_Reps.txt"
COST_CRITERIA_PATH = f"{CONFIGS_DIR}/Cost_Criteria.txt"
