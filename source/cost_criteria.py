from dataclasses import dataclass


# CostCriteria class to hold the classification terms parsed out of Cost_Criteria.txt. It is an
# immutable value: InvoiceAppFileIO.parse_cost_criteria_file() returns a fresh one on every parse,
# and a reloaded config reaches the InvoiceProcessor only through set_cost_criteria(), so no two
# objects ever share state that one of them mutates. The defaults are the "nothing parsed yet" value.
@dataclass(frozen=True)
class CostCriteria:
    # fmt:off
    labor: tuple[str, ...]              = ()        # Terms that mark a payment line as a labor cost
    labor_exclusions: tuple[str, ...]   = ()        # Terms that stop a matched line from being labor
    shipping: tuple[str, ...]           = ()        # Terms that mark a payment line as a shipping cost
    # fmt:on
