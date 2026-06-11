from decimal import Decimal

# Shared constants used across the application. Defined once here and imported
# wherever needed so values like DECIMAL_ZERO are never redefined per-module.

DECIMAL_ZERO = Decimal("0.00")
