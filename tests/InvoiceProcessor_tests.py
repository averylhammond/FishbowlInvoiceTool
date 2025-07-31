import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from source.InvoiceProcessor import InvoiceProcessor
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.Invoice import Invoice
from source.globals import DECIMAL_ZERO


###############################################################################
###                        InvoiceProcessor -> Test Fixture                 ###
###############################################################################
@pytest.fixture
def mock_file_io():
    """
    Returns a mocked InvoiceAppFileIO object
    """
    return MagicMock(spec=InvoiceAppFileIO)


@pytest.fixture
def invoice_processor(mock_file_io):
    """
    Returns a configured InvoiceProcessor instance

    Args:
        mock_file_io (unittest.mock.MagicMock): The mock InvoiceAppFileIO object
    """
    return InvoiceProcessor(
        file_io_controller=mock_file_io,
        labor_criteria=["LABOR"],
        labor_exclusions=["NO-LABOR"],
        shipping_criteria=["SHIPPING"],
    )


@pytest.fixture
def invoice():
    """
    Returns a mock Invoice object with a mocked first page
    """
    mock_invoice = Invoice()
    mock_invoice.page_contents = [
        "Customer: Acme Corp\nPO Number: PO12345S\nS12345\n01/01/2025"
    ]

    return mock_invoice


###############################################################################
###                Tests InvoiceProcessor -> populate_invoice()             ###
###############################################################################
def test_populate_invoice_raises_on_none(invoice_processor):
    """
    Verifies that populate_invoice raises an error if invoice is None

    Args:
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
    """

    # Call populate_invoice() with Invoice=None
    with pytest.raises(ValueError) as exception:
        invoice_processor.populate_invoice(
            invoice=None, sales_reps={}, payment_terms=[]
        )

    # Ensure that an exception is raised with the correct error message
    assert "Cannot parse a None invoice object" in str(exception)


@patch("source.InvoiceProcessor.find_sales_rep", return_value="Rep Name")
@patch("source.InvoiceProcessor.find_payment_terms", return_value="Net 30")
@patch("source.InvoiceProcessor.search_text_by_re")
def test_populate_invoice_populates_fields(
    mock_search_text_by_re,
    mock_find_payment_terms,
    mock_find_sales_rep,
    invoice_processor,
    invoice,
):
    """
    Verifies that all expected fields are populated correctly on the invoice

    Args:
        mock_search_text_by_re (unittest.mock.MagicMock): The mocked search_text_by_re function
        mock_find_payment_terms (unittest.mock.MagicMock): The mocked mock_find_payment_terms function
        mock_find_sales_rep (unittest.mock.MagicMock): The mocked mock_find_sales_rep function
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
        invoice (pytest.fixture): Test fixture to create the Invoice object
    """

    # Setup mocked return values for sequential calls to search_text_by_re
    mock_search_text_by_re.side_effect = [
        "S12345",
        "01/01/2025",
        "Customer: Acme Corp",
        "PO Number: PO12345S",
    ]

    sales_reps = {"REP1": "Rep Name"}
    payment_terms = ["Net 30"]

    # Call populate_invoice()
    invoice_processor.populate_invoice(invoice, sales_reps, payment_terms)

    # Verify that each of the following Invoice attributes were populated from the
    # first page of the invoice with serach_text_by_re() calls
    assert invoice.order_number == "S12345"
    assert invoice.date == "01/01/2025"
    assert invoice.customer_name == "Acme Corp"
    assert invoice.po_number == "PO12345"

    # Verify that populate_invoice() was able to populate the payment terms by calling
    # find_payment_terms()
    assert invoice.payment_terms == "Net 30"

    # Verify that populate_invoice() was able to populate the sales rep by calling
    # find_sales_rep()
    assert invoice.sales_rep == "Rep Name"

    # Verify that search_text_by_re() was called 4 times, since there are four
    # Invoice attributes on the first page
    assert mock_search_text_by_re.call_count == 4

    # Verify that find_payment_terms() was called once, since the payment terms
    # are on the first page
    mock_find_payment_terms.assert_called_once_with(
        text=invoice.page_contents[0], payment_terms=payment_terms
    )

    # Verify that find_sales_rep() was called once, since the sales rep is on
    # the first page
    mock_find_sales_rep.assert_called_once_with(
        text=invoice.page_contents[0], sales_reps=sales_reps
    )


###############################################################################
###           Tests InvoiceProcessor -> process_payment_line()              ###
###############################################################################
def test_process_payment_line_skips_subtotal_line(invoice_processor, invoice):
    """
    Verifies that the function will not calculate a listed subtotal as a
    a quantity or hourly cost

    Args:
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
        invoice (pytest.fixture): Test fixture to create the Invoice object
    """

    # Mock the find_ea_cost() and find_hr_cost() class functions
    invoice_processor.find_ea_cost = MagicMock()
    invoice_processor.find_hr_cost = MagicMock()

    # Payment line contains the subtotal
    subtotal_line = "payment line containing subtotal"

    # Call process_payment_line() with the subtotal line
    invoice_processor.process_payment_line(
        text="some invoice text",
        line=subtotal_line,
        invoice=invoice,
        curr_line_num=2,
    )

    # Verify that no functions were called to determine the cost, since the line
    # contains the subtotal and not a payment item
    invoice_processor.find_ea_cost.assert_not_called()
    invoice_processor.find_hr_cost.assert_not_called()


@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_process_payment_line_labor_cost(
    _mock_format_currency, invoice_processor, invoice
):
    """
    Verifies that a payment line with labor criteria updates the invoice's labor cost
    and subtotal correctly

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
        invoice (pytest.fixture): Test fixture to create the Invoice object
    """

    # Mock functions to return a valid quantity cost (find_ea_cost)
    invoice_processor.find_ea_cost = MagicMock(return_value=Decimal("10.00"))
    invoice_processor.find_hr_cost = MagicMock(return_value=DECIMAL_ZERO)

    # Mock functions to determine this is a labor cost
    invoice_processor.search_for_labor_criteria = MagicMock(return_value=True)
    invoice_processor.search_for_shipping = MagicMock(return_value=False)

    # Call process_payment_line() with a labor cost line
    invoice_processor.process_payment_line(
        text="1 LABOR Install\n2 Next Line",
        line="1 LABOR Install",
        invoice=invoice,
        curr_line_num=1,
    )

    # Verify that the labor cost was added
    assert invoice.labor_cost == Decimal("10.00")
    assert invoice.subtotal == Decimal("10.00")

    # Verify that file_io_controller -> print_to_debug_file() was called once
    invoice_processor.file_io_controller.print_to_debug_file.assert_called_once()

    # Verify the contents of the debug print
    assert (
        "LABOR COST"
        in invoice_processor.file_io_controller.print_to_debug_file.call_args[
            1
        ]["contents"]
    )


@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_process_payment_line_shipping_cost(
    _mock_format_currency, invoice_processor, invoice
):
    """
    Verifies that a payment line with shipping criteria updates the invoice's shipping cost
    and subtotal correctly

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
        invoice (pytest.fixture): Test fixture to create the Invoice object
    """

    # Mock functions to return a valid hourly cost (find_hr_cost)
    invoice_processor.find_ea_cost = MagicMock(return_value=DECIMAL_ZERO)
    invoice_processor.find_hr_cost = MagicMock(return_value=Decimal("20.00"))

    # Mock functions to determine this is a shipping cost
    invoice_processor.search_for_labor_criteria = MagicMock(return_value=False)
    invoice_processor.search_for_shipping = MagicMock(return_value=True)

    # Call process_payment_line() with a shipping cost line
    invoice_processor.process_payment_line(
        text="1 SHIPPING UPS Ground\n2 Next Line",
        line="1 SHIPPING UPS Ground",
        invoice=invoice,
        curr_line_num=1,
    )

    # Verify that the shipping cost was added
    assert invoice.shipping_cost == Decimal("20.00")
    assert invoice.subtotal == Decimal("20.00")

    # Verify that file_io_controller -> print_to_debug_file() was called once
    invoice_processor.file_io_controller.print_to_debug_file.assert_called_once()

    # Verify the contents of the debug print
    assert (
        "SHIPPING COST"
        in invoice_processor.file_io_controller.print_to_debug_file.call_args[
            1
        ]["contents"]
    )


@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_process_payment_line_material_cost(
    _mock_format_currency, invoice_processor, invoice
):
    """
    Verifies that a payment line not matching labor or shipping is categorized as material cost

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
        invoice (pytest.fixture): Test fixture to create the Invoice object
    """

    # Mock functions to return a valid quantity cost (find_ea_cost)
    invoice_processor.find_ea_cost = MagicMock(return_value=Decimal("50.00"))
    invoice_processor.find_hr_cost = MagicMock(return_value=DECIMAL_ZERO)

    # Mock functions to determine this is neither a labor or shipping cost
    invoice_processor.search_for_labor_criteria = MagicMock(return_value=False)
    invoice_processor.search_for_shipping = MagicMock(return_value=False)

    # Call process_payment_line()
    invoice_processor.process_payment_line(
        text="1 BRACKETS METAL\n2 Next Line",
        line="1 BRACKETS METAL",
        invoice=invoice,
        curr_line_num=1,
    )

    # Verify that the material cost was added since no labor or shipping criteria
    # were present in the line
    assert invoice.material_cost == Decimal("50.00")
    assert invoice.subtotal == Decimal("50.00")

    #  Verify that file_io_controller -> print_to_debug_file() was called once
    invoice_processor.file_io_controller.print_to_debug_file.assert_called_once()

    # Verify the contents of the debug print
    assert (
        "MATERIAL COST"
        in invoice_processor.file_io_controller.print_to_debug_file.call_args[
            1
        ]["contents"]
    )


def test_process_payment_line_skips_if_no_cost_found(
    invoice_processor, invoice
):
    """
    Verifies that process_payment_line returns early if no valid cost is found

    Args:
        invoice_processor (pytest.fixture): Test fixture to create the InvoiceProcessor object
        invoice (pytest.fixture): Test fixture to create the Invoice object
    """

    # Mock functions such that no cost values were found
    invoice_processor.find_ea_cost = MagicMock(return_value=DECIMAL_ZERO)
    invoice_processor.find_hr_cost = MagicMock(return_value=DECIMAL_ZERO)

    # Call process_payment_line() with a normal line but no cost
    invoice_processor.process_payment_line(
        text="2 COMPONENT LABEL\n3 Next Line",
        line="2 COMPONENT LABEL",
        invoice=invoice,
        curr_line_num=2,
    )

    # Verify that no values were added to invoice
    assert invoice.subtotal == DECIMAL_ZERO
    assert invoice.material_cost == DECIMAL_ZERO
    assert invoice.labor_cost == DECIMAL_ZERO
    assert invoice.shipping_cost == DECIMAL_ZERO


###############################################################################
###               Tests InvoiceProcessor -> find_ea_cost()                  ###
###############################################################################
@patch("source.InvoiceProcessor.search_payment_line")
@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_find_ea_cost_returns_first_valid_cost(
    _mock_format_currency, mock_search_payment_line, invoice_processor
):
    """
    Verifies that find_ea_cost() returns the first valid quantity cost found in the payment lines

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        mock_search_payment_line (unittest.mock.MagicMock): Mocked search_payment_line function
        invoice_processor (pytest.fixture): The InvoiceProcessor instance under test
    """

    # Mock the first call to search_payment_line() to return 45.60
    mock_search_payment_line.side_effect = [Decimal("45.60")]

    # Create a payment line containing the string
    payment_lines = "2 anchor bolt ea $45.60"

    # Call find_ea_cost() with the payment line
    cost = invoice_processor.find_ea_cost(payment_lines)

    # Verify that the correct cost is found
    assert cost == Decimal("45.60")


@patch("source.InvoiceProcessor.search_payment_line")
@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_find_ea_cost_returns_zero_when_no_match(
    _mock_format_currency, mock_search_payment_line, invoice_processor
):
    """
    Verifies that find_ea_cost() returns the first valid quantity cost found in the payment lines

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        mock_search_payment_line (unittest.mock.MagicMock): Mocked search_payment_line function
        invoice_processor (pytest.fixture): The InvoiceProcessor instance under test
    """

    # Mock the first call to search_payment_line() to return DECIMAL_ZERO,
    # indicating that there was no match for the given regex
    mock_search_payment_line.side_effect = [DECIMAL_ZERO]

    # Create a payment line containing no valid quantity cost
    payment_lines = "2 anchor bolt no quantity cost"

    # Call find_ea_cost() with the payment line
    cost = invoice_processor.find_ea_cost(payment_lines)

    # Verify that no cost was found
    assert cost == DECIMAL_ZERO


###############################################################################
###               Tests InvoiceProcessor -> find_hr_cost()                  ###
###############################################################################
@patch("source.InvoiceProcessor.search_payment_line")
@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_find_hr_cost_returns_first_valid_cost(
    _mock_format_currency, mock_search_payment_line, invoice_processor
):
    """
    Verifies that find_hr_cost() returns the first valid hourly cost found in the payment lines

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        mock_search_payment_line (unittest.mock.MagicMock): Mocked search_payment_line function
        invoice_processor (pytest.fixture): The InvoiceProcessor instance under test
    """

    # Mock the first call to search_payment_line() to return 45.60
    mock_search_payment_line.side_effect = [Decimal("45.60")]

    # Create a payment line containing the string
    payment_lines = "UPS shipping hr $45.60"

    # Call find_hr_cost() with the payment line
    cost = invoice_processor.find_hr_cost(payment_lines)

    # Verify that the correct cost is found
    assert cost == Decimal("45.60")


@patch("source.InvoiceProcessor.search_payment_line")
@patch(
    "source.InvoiceProcessor.format_currency",
    side_effect=lambda value: Decimal(value),
)
def test_find_hr_cost_returns_zero_when_no_match(
    _mock_format_currency, mock_search_payment_line, invoice_processor
):
    """
    Verifies that find_hr_cost() returns the first valid hourly cost found in the payment lines

    Args:
        _mock_format_currency (unittest.mock.MagicMock): Mocked format_currency function
        mock_search_payment_line (unittest.mock.MagicMock): Mocked search_payment_line function
        invoice_processor (pytest.fixture): The InvoiceProcessor instance under test
    """

    # Mock the first call to search_payment_line() to return DECIMAL_ZERO,
    # indicating that there was no match for the given regex
    mock_search_payment_line.side_effect = [DECIMAL_ZERO]

    # Create a payment line containing no valid quantity cost
    payment_lines = "UPS shipping no hourly cost"

    # Call find_hr_cost() with the payment line
    cost = invoice_processor.find_hr_cost(payment_lines)

    # Verify that no cost was found
    assert cost == DECIMAL_ZERO
