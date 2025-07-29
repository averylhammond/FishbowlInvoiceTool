import pytest  # TODO: Is there a way to separate out pytest in the requirements.txt to only include for debug builds? Or something like that
from decimal import Decimal
from source.processor_utilities import *

from source.globals import DECIMAL_ZERO


###############################################################################
###          Tests for processor_utilities -> search_text_by_re()           ###
###############################################################################
def test_search_text_by_re_order_number_correct_format():
    """
    Tests that the function search_text_by_re can successfully extract an order number
    where the string is formatted correctly

    The expected format is 'SXXXXX' where x is a non zero integer
    """

    # Expected format
    regex = r"S(\d{5})"

    # Verify the order number can be extracted
    text = "S12345 - CORRECT ORDER NUMBER FORMAT"
    assert search_text_by_re(text=text, regex=regex) == "S12345"


def test_search_text_by_re_order_number_wrong_format():
    """
    Tests that the function search_text_by_re will return an empty string (indicating
    failure) if a regex match cannot be made when searching for an order number

    The expected format is 'SXXXXX' where x is a non zero integer
    """

    # Expected format
    regex = r"S(\d{5})"

    # Verify that no valid order number could be extracted since 'S' is not followed by 5 digits
    text = "S1234 - WRONG ORDER NUMBER FORMAT"
    assert search_text_by_re(text=text, regex=regex) == ""

    # Verify that no valid order number can be extracted since 'S' is not followed by 5 digits
    text = "12S34 - WRONG ORDER NUMBER FORMAT"
    assert search_text_by_re(text=text, regex=regex) == ""


def test_search_text_by_re_invoice_date_correct_format():
    """
    Tests that the function search_text_by_re can successfully extract an invoice date
    where string is formatted correctly

    The expected format is 'mm/dd/yyyy' where mm is the month, dd is the day, and yyyy is the year
    """

    # Expected format
    regex = r"\d{2}/\d{2}/\d{4}"

    # Verify the invoice date can be extracted
    text = "07/28/2025 - CORRECT DATE FORMAT"
    assert search_text_by_re(text=text, regex=regex) == "07/28/2025"


def test_search_text_by_re_invoice_date_wrong_format():
    """
    Tests that the function search_text_by_re will return an empty string (indicating
    failure) if a regex match cannot be made when searching for an invoice date

    The expected format is 'mm/dd/yyyy' where mm is the month, dd is the day, and yyyy is the year
    """

    # Expected format
    regex = r"\d{2}/\d{2}/\d{4}"

    # Verify that no valid order number can be extracted since there are not two digits for the month
    text = "date 7/28/2025 - WRONG DATE FORMAT"
    assert search_text_by_re(text=text, regex=regex) == ""

    # Verify that no valid order number can be extracted since there are more than two digits for the day
    text = "date 07/2/2025 - WRONG DATE FORMAT"
    assert search_text_by_re(text=text, regex=regex) == ""

    # Verify that no valid order number can be extracted since there are less than four digits for the year
    text = "date 07/28/25 - WRONG DATE FORMAT"
    assert search_text_by_re(text=text, regex=regex) == ""

    # Verify that no valid order number can be extracted since '-' is as a delimiter
    text = "date 07-28-2025 - WRONG DATE FORMAT"
    assert search_text_by_re(text=text, regex=regex) == ""


def test_search_text_by_re_customer_name_correct_format():
    """
    Tests that the function search_text_by_re can successfully extract a customer
    name when the string is formatted correctly

    The expected format is 'Customer: x' where x is the customer name. Note that
    there can be no characters after the name, there must be a newline for it to
    match correctly
    """

    # Expected format
    regex = r"Customer: .+"

    # Verify the invoice date can be extracted
    text = "CORRECT CUSTOMER NAME FORMAT - Customer: FishbowlInvoiceProcessor"
    assert (
        search_text_by_re(text=text, regex=regex)
        == "Customer: FishbowlInvoiceProcessor"
    )


def test_search_text_by_re_customer_name_wrong_format():
    """
    Tests that the function search_text_by_re will return an empty string (indicating
    failure) if a regex match cannot be made when searching for the customer name

    The expected format is 'Customer: x' where x is the customer name. Note that
    there can be no characters after the name, there must be a newline for it to
    match correctly
    """

    # Expected format
    regex = r"Customer: .+"

    # Verify that no valid customer name can be extracted since 'Customer:' does not exist in the string
    text = "WRONG CUSTOMER NAME FORMAT - Customerr: FishbowlInvoiceProcessor"
    assert search_text_by_re(text=text, regex=regex) == ""

    # Verify that no valid customer name can be extracted since no colon exists in the string
    text = "WRONG CUSTOMER NAME FORMAT - Customer FishbowlInvoiceProcessor"
    assert search_text_by_re(text=text, regex=regex) == ""

    # SPECIAL CASE
    # Verify that characters after the name are still matched
    text = "WRONG CUSTOMER NAME FORMAT BUT STILL MATCHES - Customer: FishbowlInvoiceProcessor - afterwards"
    assert (
        search_text_by_re(text=text, regex=regex)
        == "Customer: FishbowlInvoiceProcessor - afterwards"
    )


def test_search_text_by_re_po_number_correct_format():
    """
    Tests that the function search_text_by_re can successfully extract a PO number
    when the string is formatted correctly

    The expected format is 'PO Number: x' where x is the PO Number. Note that
    there can be no characters after the number, there must be a newline for it to
    match correctly
    """

    # Expected format
    regex = r"PO Number: .+"

    # Verify the PO Number can be extracted
    text = "CORRECT PO NUMBER FORMAT - PO Number: N12345"
    assert search_text_by_re(text=text, regex=regex) == "PO Number: N12345"

    # Verify the PO Number is extracted with all text appearing after it as well
    # This requires special handling in the function that calls search_text_by_re
    # in order to retrieve the PO number from the string
    text = "CORRECT PO NUMBER FORMAT - PO Number: N12345 - ADDITIONAL TEXT"
    assert (
        search_text_by_re(text=text, regex=regex)
        == "PO Number: N12345 - ADDITIONAL TEXT"
    )


def test_search_text_by_re_po_number_wrong_format():
    """
    Tests that the function search_text_by_re will return an empty string (indicating
    failure) if a regex match cannot be made when searching for the customer name

    The expected format is 'PO Number: x' where x is the PO Number. Note that
    there can be no characters after the number, there must be a newline for it to
    match correctly
    """

    # Expected format
    regex = r"PO Number: .+"

    # Verify that no valid customer name can be extracted since 'PO Numberr:' does not exist in the string
    text = "WRONG PO NUMBER FORMAT - PO Numberr: N12345"
    assert search_text_by_re(text=text, regex=regex) == ""

    # Verify that no valid PO Number can be extracted since no colon exists in the string
    text = "WRONG PO NUMBER FORMAT - PO Number N12345"
    assert search_text_by_re(text=text, regex=regex) == ""


###############################################################################
###        Tests for processor_utilities -> search_payment_line()           ###
###############################################################################
def test_search_payment_line_quantity_correct_format():
    """
    Tests that the function search_payment_line can successfully extract an a quantity
    order cost from an invoice payment line

    The expected format is '$x y ea $ z" where x is the unit cost, y is the quantity of
    the item sold, and z is the total cost of the payment line ( x * y )
    """

    # Expected format
    regex = r"[0-9]+\s*ea(.*)"

    # Verify the quantity cost can be extracted
    line = "$59.65 1ea $ 59.65"
    assert search_payment_line(line=line, regex=regex) == Decimal("59.65")

    # Verify the quantity cost can be extracted with extra spaces
    line = "$ 59.65 1 ea $ 59.65"
    assert search_payment_line(line=line, regex=regex) == Decimal("59.65")

    # Verify the quantity cost can be extracted with 2 digit quantities
    line = "$ 59.65 10 ea $ 596.50"
    assert search_payment_line(line=line, regex=regex) == Decimal("596.50")

    # Verify the quantity cost can be extracted with 3 digit quantities
    line = "$ 59.65 100 ea $ 5965.00"
    assert search_payment_line(line=line, regex=regex) == Decimal("5965.00")

    # Verify the quantity cost can be extracted with 4 digit quantities
    line = "$ 59.65 1000 ea $ 59650.00"
    assert search_payment_line(line=line, regex=regex) == Decimal("59650.00")


# def test_search_payment_line_valid():
#     line = "Total payment: $1,234.56"
#     regex = r"\$[\d,]+\.\d{2}"
#     assert search_payment_line(line, regex) == Decimal("1234.56")


# def test_search_payment_line_invalid():
#     line = "Total payment: N/A"
#     regex = r"\$[\d,]+\.\d{2}"
#     assert search_payment_line(line, regex) == DECIMAL_ZERO


# def test_find_payment_terms_found():
#     text = "Net 30 payment terms apply"
#     payment_terms = ["Net 15", "Net 30", "Due on receipt"]
#     assert find_payment_terms(text, payment_terms) == "Net 30"


# def test_find_payment_terms_not_found():
#     text = "Payment due next week"
#     payment_terms = ["Net 15", "Net 30", "Due on receipt"]
#     assert find_payment_terms(text, payment_terms) == ""


# def test_find_sales_rep_found():
#     text = "Sold by rep123"
#     sales_reps = {"rep123": "Alice Johnson", "rep456": "Bob Smith"}
#     assert find_sales_rep(text, sales_reps) == "Alice Johnson"


# def test_find_sales_rep_not_found():
#     text = "Sold by rep999"
#     sales_reps = {"rep123": "Alice Johnson", "rep456": "Bob Smith"}
#     assert find_sales_rep(text, sales_reps) == ""


# @pytest.mark.parametrize(
#     "input_val,expected",
#     [
#         ("123.45", Decimal("123.45")),
#         ("123.456", Decimal("123.46")),
#         ("123", Decimal("123.00")),
#         (123.1, Decimal("123.10")),
#         (Decimal("5.555"), Decimal("5.56")),
#     ],
# )
# def test_format_currency_valid(input_val, expected):
#     assert format_currency(input_val) == expected


# @pytest.mark.parametrize("input_val", ["abc", None, object()])
# def test_format_currency_invalid(input_val):
#     assert format_currency(input_val) == DECIMAL_ZERO
