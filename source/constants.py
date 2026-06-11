from decimal import Decimal

DECIMAL_ZERO = Decimal("0.00")

# Application file paths, relative to the executable's current working directory.

# Base directories. The specific file paths below are composed from these.
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
