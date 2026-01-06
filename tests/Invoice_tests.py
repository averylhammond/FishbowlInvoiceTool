import pytest
from decimal import Decimal
from source.Invoice import *

from source.globals import DECIMAL_ZERO


###############################################################################
###                        Tests Invoice -> Constructor                     ###
###############################################################################
def test_invoice_initialization():
    """
    Tests that the default initialization of the Invoice() object will correctly
    populate all defaut values to class attributes
    """

    # Create default instance of Invoice class
    invoice = Invoice()

    # Check that all string fields are initialized to an empty string
    assert invoice.customer_name == "wrong"
    assert invoice.date == ""
    assert invoice.order_number == ""
    assert invoice.po_number == ""
    assert invoice.payment_terms == ""
    assert invoice.sales_rep == ""

    # Check that all Decimal() fields are initialized to 0.0
    assert invoice.labor_cost == DECIMAL_ZERO
    assert invoice.material_cost == DECIMAL_ZERO
    assert invoice.shipping_cost == DECIMAL_ZERO
    assert invoice.subtotal == DECIMAL_ZERO
    assert invoice.sales_tax == DECIMAL_ZERO
    assert invoice.total == DECIMAL_ZERO
    assert invoice.listed_total == DECIMAL_ZERO

    # Check that the list of strings is initialized to an empty list
    assert invoice.page_contents == []


###############################################################################
###                  Tests Invoice -> to_formatted_string()                 ###
###############################################################################
def test_invoice_to_formatted_string_default():
    """
    Tests that to_formatted_string() will correctly print default values when
    the Invoice class is initialized as default
    """

    # Create default instance of Invoice class
    invoice = Invoice()

    # Output all default attributes as a formatted string
    output = invoice.to_formatted_string()

    # Verify all default fields appear in the output string
    assert "Customer Name:" in output
    assert "Invoice Date:" in output
    assert "Order Number:" in output
    assert "PO Number:" in output
    assert "Payment Terms:" in output
    assert "Sales Rep:" in output
    assert "Labor Cost: $0.0" in output
    assert "Material Cost: $0.0" in output
    assert "Shipping Cost: $0.0" in output
    assert "Subtotal: $0.0" in output
    assert "Sales Tax: $0.0" in output
    assert "Listed Total: $0.0" in output


def test_invoice_to_formatted_string_values():
    """
    Tests that to_formatted_string() will correctly print the set values
    of all invoice attributes
    """

    # Create an Invoice object
    invoice = Invoice()

    # Specify custom invoice attributes
    invoice.customer_name = "Alice"
    invoice.date = "07/28/2025"
    invoice.order_number = "S12345"
    invoice.po_number = "PO98765"
    invoice.payment_terms = "Up Front"
    invoice.sales_rep = "Bob"
    invoice.labor_cost = Decimal("100.00")
    invoice.material_cost = Decimal("200.00")
    invoice.shipping_cost = Decimal("50.00")
    invoice.subtotal = Decimal("350.00")
    invoice.sales_tax = Decimal("35.00")
    invoice.total = Decimal("385.00")
    invoice.listed_total = Decimal("385.00")

    # Get the invoice attributes as a formatted string
    output = invoice.to_formatted_string()

    # Verify all fields appear in the output string
    assert "Customer Name: Alice" in output
    assert "Invoice Date: 07/28/2025" in output
    assert "Order Number: S12345" in output
    assert "PO Number: PO98765" in output
    assert "Payment Terms: Up Front" in output
    assert "Sales Rep: Bob" in output
    assert "Labor Cost: $100.00" in output
    assert "Material Cost: $200.00" in output
    assert "Shipping Cost: $50.00" in output
    assert "Subtotal: $350.00" in output
    assert "Sales Tax: $35.00" in output
    assert "Listed Total: $385.00" in output
