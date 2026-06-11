from decimal import Decimal

# Shared constants used across the application. Defined once here and imported
# wherever needed so values like DECIMAL_ZERO are never redefined per-module.

DECIMAL_ZERO = Decimal("0.00")

# Application file paths, relative to the executable's current working directory.
# Defined once here so they are not redefined as literals throughout the codebase.
DEBUG_LOG_PATH = "logs/debug.txt"
RESULTS_LOG_PATH = "logs/results.txt"
INVOICES_PATH = "Invoices"
PAYMENT_TERMS_PATH = "Configs/Payment_Terms.txt"
SALES_REPS_PATH = "Configs/Sales_Reps.txt"
COST_CRITERIA_PATH = "Configs/Cost_Criteria.txt"
