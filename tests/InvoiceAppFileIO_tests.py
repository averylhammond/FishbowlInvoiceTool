import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, call, MagicMock

from source.Invoice import Invoice
from source.InvoiceAppFileIO import *
from source.constants import (
    SALES_REPS_PATH,
    PAYMENT_TERMS_PATH,
    COST_CRITERIA_PATH,
)


###############################################################################
###                      InvoiceAppFileIO -> Test Fixture                   ###
###############################################################################
@pytest.fixture
def file_io():
    """
    Test fixture to set up an InvoiceAppFileIO object for testing to maximize
    code reuse. The error reporter is a mock so failure paths can assert that the
    failure was surfaced to the user.
    """

    return InvoiceAppFileIO(report_error=MagicMock())


###############################################################################
###              Tests InvoiceAppFileIO -> reset_debug_file()               ###
###############################################################################
@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_reset_debug_file_file_exists(mock_debug_path, file_io):
    """
    Tests that reset_debug_file() ensures the log directory exists and deletes the
    debug log file when it is present.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The debug file exists on disk
    mock_debug_path.is_file.return_value = True

    file_io.reset_debug_file()

    # The log directory is ensured and the existing debug file is deleted
    mock_debug_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_debug_path.unlink.assert_called_once_with()


@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_reset_debug_file_file_doesnt_exist(mock_debug_path, file_io):
    """
    Tests that reset_debug_file() does not delete the debug log file when it does
    not exist, while still ensuring the log directory exists.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The debug file does not exist on disk
    mock_debug_path.is_file.return_value = False

    file_io.reset_debug_file()

    # The directory is ensured but nothing is deleted
    mock_debug_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_debug_path.unlink.assert_not_called()


@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_reset_debug_file_reports_on_error(mock_debug_path, file_io):
    """
    Tests that reset_debug_file() fails gracefully, surfacing the failure through
    the error reporter instead of raising when the filesystem operation fails.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Creating the log directory fails
    mock_debug_path.parent.mkdir.side_effect = OSError("permission denied")

    # No exception is raised, and the failure is reported to the user
    file_io.reset_debug_file()
    file_io.report_error.assert_called_once()


###############################################################################
###              Tests InvoiceAppFileIO -> reset_results_file()             ###
###############################################################################
@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_reset_results_file_file_exists(mock_results_path, file_io):
    """
    Tests that reset_results_file() ensures the log directory exists and deletes
    the results log file when it is present.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The results file exists on disk
    mock_results_path.is_file.return_value = True

    file_io.reset_results_file()

    # The log directory is ensured and the existing results file is deleted
    mock_results_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_results_path.unlink.assert_called_once_with()


@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_reset_results_file_file_doesnt_exist(mock_results_path, file_io):
    """
    Tests that reset_results_file() does not delete the results log file when it
    does not exist, while still ensuring the log directory exists.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The results file does not exist on disk
    mock_results_path.is_file.return_value = False

    file_io.reset_results_file()

    # The directory is ensured but nothing is deleted
    mock_results_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_results_path.unlink.assert_not_called()


@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_reset_results_file_reports_on_error(mock_results_path, file_io):
    """
    Tests that reset_results_file() fails gracefully, surfacing the failure through
    the error reporter instead of raising when the filesystem operation fails.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Deleting the existing results file fails
    mock_results_path.is_file.return_value = True
    mock_results_path.unlink.side_effect = OSError("file is locked")

    # No exception is raised, and the failure is reported to the user
    file_io.reset_results_file()
    file_io.report_error.assert_called_once()


###############################################################################
###             Tests InvoiceAppFileIO -> print_to_debug_file()             ###
###############################################################################
@patch("builtins.open", new_callable=mock_open)
@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_print_to_debug_file_appends(mock_debug_path, mock_file, file_io):
    """
    Tests that print_to_debug_file() ensures the log directory exists, opens the
    debug log in append mode, and writes the contents with a trailing newline.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    file_io.print_to_debug_file("some debug message")

    # The directory is ensured and the contents are appended
    mock_debug_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file.assert_called_once_with(file=mock_debug_path, mode="a")
    mock_file().write.assert_called_once_with("some debug message\n")


@patch("builtins.open", side_effect=OSError("disk full"))
@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_print_to_debug_file_reports_on_error(mock_debug_path, _mock_file, file_io):
    """
    Tests that print_to_debug_file() fails gracefully, surfacing the failure
    through the error reporter instead of raising when the write fails.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # No exception is raised, and the failure is reported to the user
    file_io.print_to_debug_file("some debug message")
    file_io.report_error.assert_called_once()


###############################################################################
###        Tests InvoiceAppFileIO -> print_invoice_to_output_file()         ###
###############################################################################
@patch("builtins.open", new_callable=mock_open)
@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_print_invoice_to_output_file_overwrites_by_default(
    mock_results_path, mock_file, file_io
):
    """
    Tests that print_invoice_to_output_file() ensures the log directory exists,
    opens the results log in write mode (overwriting) by default, and writes the
    invoice's formatted string.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Build a mock invoice whose formatted string is a known value
    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.to_formatted_string.return_value = "formatted invoice"

    file_io.print_invoice_to_output_file(mock_invoice)

    # The directory is ensured and the invoice is written in overwrite mode
    mock_results_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file.assert_called_once_with(file=mock_results_path, mode="w")
    mock_file().write.assert_called_once_with("formatted invoice")


@patch("builtins.open", new_callable=mock_open)
@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_print_invoice_to_output_file_appends_when_requested(
    mock_results_path, mock_file, file_io
):
    """
    Tests that print_invoice_to_output_file() opens the results log in append mode
    when append_output is True and writes the invoice's formatted string.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Build a mock invoice whose formatted string is a known value
    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.to_formatted_string.return_value = "formatted invoice"

    file_io.print_invoice_to_output_file(mock_invoice, append_output=True)

    # The invoice is written in append mode
    mock_file.assert_called_once_with(file=mock_results_path, mode="a")
    mock_file().write.assert_called_once_with("formatted invoice")


@patch("builtins.open", side_effect=OSError("disk full"))
@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_print_invoice_to_output_file_reports_on_error(
    mock_results_path, _mock_file, file_io
):
    """
    Tests that print_invoice_to_output_file() fails gracefully, surfacing the
    failure through the error reporter instead of raising when the write fails.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    mock_invoice = MagicMock(spec=Invoice)

    # No exception is raised, and the failure is reported to the user
    file_io.print_invoice_to_output_file(mock_invoice)
    file_io.report_error.assert_called_once()


###############################################################################
###              Tests InvoiceAppFileIO -> read_invoice_file()              ###
###############################################################################
@patch("source.InvoiceAppFileIO.PyPDF2.PdfReader")
def test_read_invoice_file_extracts_each_page(mock_reader, file_io):
    """
    Tests that read_invoice_file() returns the extracted text of each page in the
    PDF, in order.

    Args:
        mock_reader (unittest.mock.MagicMock): Mocks PyPDF2.PdfReader
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The PDF reader yields two pages with known text
    first_page = MagicMock()
    first_page.extract_text.return_value = "page one"
    second_page = MagicMock()
    second_page.extract_text.return_value = "page two"
    mock_reader.return_value.pages = [first_page, second_page]

    pages = file_io.read_invoice_file(Path("invoice.pdf"))

    # The reader is given the invoice path and each page's text is returned in order
    mock_reader.assert_called_once_with(stream=Path("invoice.pdf"))
    assert pages == ["page one", "page two"]


@patch(
    "source.InvoiceAppFileIO.PyPDF2.PdfReader",
    side_effect=OSError("file not found"),
)
def test_read_invoice_file_reports_and_returns_empty_on_error(mock_reader, file_io):
    """
    Tests that read_invoice_file() fails gracefully, surfacing the failure through
    the error reporter and returning an empty list when the PDF cannot be read.

    Args:
        mock_reader (unittest.mock.MagicMock): Mocks PyPDF2.PdfReader to raise
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    pages = file_io.read_invoice_file(Path("missing.pdf"))

    # No exception is raised, an empty list is returned, and the failure is reported
    assert pages == []
    file_io.report_error.assert_called_once()


###############################################################################
###          Tests InvoiceAppFileIO -> parse_sales_reps_config()            ###
###############################################################################
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""* comment line
SR1=John Smith
SR2=Alice Johnson

* another comment
SR3=Bob Stone
""",
)
def test_parse_sales_reps_config_success(mock_file, file_io):
    """
    Tests that parse_sales_reps_config() correctly parses valid entries
    and ignores comments and empty lines.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Call parse_sales_reps_config() and save the return
    sales_reps = file_io.parse_sales_reps_config()

    # Expect the function to correctly parse the config file
    expected_sales_reps = {
        "SR1": "John Smith",
        "SR2": "Alice Johnson",
        "SR3": "Bob Stone",
    }
    assert sales_reps == expected_sales_reps

    # Ensure that the file was opened in reading mode
    mock_file.assert_called_once_with(file=SALES_REPS_PATH, mode="r")


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="",
)
def test_parse_sales_reps_config_empty_file(mock_file, file_io):
    """
    Tests that parse_sales_reps_config() returns an empty dictionary
    when the config file contains no entries.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Call parse_sales_reps_config() and save the return
    sales_reps = file_io.parse_sales_reps_config()

    # Expect an empty dictionary to be returned
    assert sales_reps == {}

    # Ensure the file was opened in reading mode
    mock_file.assert_called_once_with(file=SALES_REPS_PATH, mode="r")


@patch("builtins.open", side_effect=OSError("file not found"))
def test_parse_sales_reps_config_reports_on_error(_mock_file, file_io):
    """
    Tests that parse_sales_reps_config() fails gracefully, surfacing the failure
    through the error reporter and returning an empty dictionary when the config
    file cannot be read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    sales_reps = file_io.parse_sales_reps_config()

    # An empty dictionary is returned and the failure is reported to the user
    assert sales_reps == {}
    file_io.report_error.assert_called_once()


###############################################################################
###        Tests InvoiceAppFileIO -> parse_payment_terms_config()           ###
###############################################################################
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""* comment
NET 30
IMMEDIATE

* another comment
DUE UPON RECEIPT
""",
)
def test_parse_payment_terms_config_success(mock_file, file_io):
    """
    Tests that parse_payment_terms_config() correctly parses valid entries
    and ignores comments and empty lines.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Call parse_payment_terms_config() and save the return
    payment_terms = file_io.parse_payment_terms_config()

    # Expect the function to correctly parse the config file
    expected_payment_terms = [
        "NET 30",
        "IMMEDIATE",
        "DUE UPON RECEIPT",
    ]
    assert payment_terms == expected_payment_terms

    # Ensure that the file was opened in reading mode
    mock_file.assert_called_once_with(file=PAYMENT_TERMS_PATH, mode="r")


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="",
)
def test_parse_payment_terms_config_empty_file(mock_file, file_io):
    """
    Tests that parse_payment_terms_config() returns an empty list
    when the config file contains no entries.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Call parse_payment_terms_config() and save the return
    payment_terms = file_io.parse_payment_terms_config()

    # Expect an empty list to be returned
    assert payment_terms == []

    # Ensure the file was opened in reading mode
    mock_file.assert_called_once_with(file=PAYMENT_TERMS_PATH, mode="r")


@patch("builtins.open", side_effect=OSError("file not found"))
def test_parse_payment_terms_config_reports_on_error(_mock_file, file_io):
    """
    Tests that parse_payment_terms_config() fails gracefully, surfacing the failure
    through the error reporter and returning an empty list when the config file
    cannot be read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    payment_terms = file_io.parse_payment_terms_config()

    # An empty list is returned and the failure is reported to the user
    assert payment_terms == []
    file_io.report_error.assert_called_once()


###############################################################################
###          Tests InvoiceAppFileIO -> add_cost_criteria_field()            ###
###############################################################################
def test_add_cost_criteria_field_appends_lists(file_io):
    """
    Tests that add_cost_criteria_field() appends lines correctly
    to the appropriate category lists.

    Args:
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Add a criterion to each list
    file_io.add_cost_criteria_field("LABOR CRITERIA", "Labor criterion 1")
    file_io.add_cost_criteria_field("LABOR EXCLUSIONS", "Labor exclusion 1")
    file_io.add_cost_criteria_field("SHIPPING CRITERIA", "Shipping criterion 1")

    # Ensure that each element was added to the list
    assert file_io.labor_criteria == ["Labor criterion 1"]
    assert file_io.labor_exclusions == ["Labor exclusion 1"]
    assert file_io.shipping_criteria == ["Shipping criterion 1"]


@patch.object(InvoiceAppFileIO, "print_to_debug_file")
def test_add_cost_criteria_field_unknown_category(mock_debug_print, file_io):
    """
    Tests that add_cost_criteria_field() calls prints a debug message
    if an unknown category is found

    Args:
        mock_debug_print (unittest.mock.MagicMock): Mocks the print_to_debug_file() function
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # To to add a criterion with an unknown category
    unknown_category = "UNKNOWN CATEGORY"
    file_io.add_cost_criteria_field(unknown_category, "some line")

    # Expect that the mocked print_to_debug_file() will be called once with the correct
    # message
    mock_debug_print.assert_called_once_with(
        f"Unknown category read out of Cost Criteria configuration file: {unknown_category}"
    )


###############################################################################
###          Tests InvoiceAppFileIO -> parse_cost_criteria_file()           ###
###############################################################################
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""
* Comment line
LABOR CRITERIA:
Labor criterion A
Labor criterion B

LABOR EXCLUSIONS:
Exclude this labor

SHIPPING CRITERIA:
Ship criterion X
Ship criterion Y
""",
)
@patch.object(InvoiceAppFileIO, "add_cost_criteria_field")
def test_parse_cost_criteria_file_calls_add_cost_criteria_field(
    mock_add_field, mock_file, file_io
):
    """
    Tests that parse_cost_criteria_file() reads the file correctly and
    calls add_cost_criteria_field() with the expected arguments.

    Args:
        mock_add_field (unittest.mock.MagicMock): Mocks the add_cost_criteria_field method
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Fixture for InvoiceAppFileIO object
    """

    # Call the method under test
    file_io.parse_cost_criteria_file()

    # Define the expected calls in order
    expected_calls = [
        call(category="LABOR CRITERIA", line="Labor criterion A"),
        call(category="LABOR CRITERIA", line="Labor criterion B"),
        call(category="LABOR EXCLUSIONS", line="Exclude this labor"),
        call(category="SHIPPING CRITERIA", line="Ship criterion X"),
        call(category="SHIPPING CRITERIA", line="Ship criterion Y"),
    ]

    # Assert the correct calls were made in order
    mock_add_field.assert_has_calls(expected_calls, any_order=False)

    # Also assert the total number of calls
    assert mock_add_field.call_count == len(expected_calls)

    # Verify file was opened for reading
    mock_file.assert_called_once_with(file=COST_CRITERIA_PATH, mode="r")


@patch("builtins.open", side_effect=OSError("file not found"))
def test_parse_cost_criteria_file_reports_on_error(_mock_file, file_io):
    """
    Tests that parse_cost_criteria_file() fails gracefully, surfacing the failure
    through the error reporter instead of raising when the config file cannot be
    read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # No exception is raised, and the failure is reported to the user
    file_io.parse_cost_criteria_file()
    file_io.report_error.assert_called_once()


@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="""LABOR CRITERIA:
Labor criterion A

LABOR EXCLUSIONS:
Exclude this labor

SHIPPING CRITERIA:
Ship criterion X
""",
)
def test_parse_cost_criteria_file_is_idempotent(_mock_file, file_io):
    """
    Tests that parse_cost_criteria_file() clears the criteria lists in place
    before parsing, so re-parsing (e.g. after the user saves an edited config)
    replaces the previous contents rather than appending duplicates.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Hold a reference to the original list objects to prove they are cleared in
    # place (kept), not reassigned to new lists
    labor_criteria_ref = file_io.labor_criteria
    labor_exclusions_ref = file_io.labor_exclusions
    shipping_criteria_ref = file_io.shipping_criteria

    # Parse twice; the second parse must not accumulate duplicate entries
    file_io.parse_cost_criteria_file()
    file_io.parse_cost_criteria_file()

    assert file_io.labor_criteria == ["Labor criterion A"]
    assert file_io.labor_exclusions == ["Exclude this labor"]
    assert file_io.shipping_criteria == ["Ship criterion X"]

    # The same list objects are reused, so the InvoiceProcessor's references stay valid
    assert file_io.labor_criteria is labor_criteria_ref
    assert file_io.labor_exclusions is labor_exclusions_ref
    assert file_io.shipping_criteria is shipping_criteria_ref


###############################################################################
###                Tests InvoiceAppFileIO -> read_text_file()               ###
###############################################################################
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data="line one\nline two\n",
)
def test_read_text_file_returns_contents(mock_file, file_io):
    """
    Tests that read_text_file() returns the full contents of the file.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    file_path = Path("Configs/Sales_Reps.txt")
    contents = file_io.read_text_file(file_path)

    # The whole file is returned and it was opened for reading
    assert contents == "line one\nline two\n"
    mock_file.assert_called_once_with(file=file_path, mode="r")


@patch("builtins.open", side_effect=OSError("file not found"))
def test_read_text_file_reports_on_error(_mock_file, file_io):
    """
    Tests that read_text_file() fails gracefully, surfacing the failure through
    the error reporter and returning an empty string when the file cannot be read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    contents = file_io.read_text_file(Path("Configs/Sales_Reps.txt"))

    # An empty string is returned and the failure is reported to the user
    assert contents == ""
    file_io.report_error.assert_called_once()


###############################################################################
###               Tests InvoiceAppFileIO -> write_text_file()               ###
###############################################################################
@patch("builtins.open", new_callable=mock_open)
def test_write_text_file_writes_contents(mock_file, file_io):
    """
    Tests that write_text_file() ensures the parent directory exists and writes
    the given contents to the file.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks the built-in open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # A mock path so the parent.mkdir call can be asserted on
    mock_path = MagicMock()
    file_io.write_text_file(mock_path, "new contents")

    # The parent directory is ensured, then the file is opened for writing and written
    mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_file.assert_called_once_with(file=mock_path, mode="w")
    mock_file().write.assert_called_once_with("new contents")


@patch("builtins.open", side_effect=OSError("permission denied"))
def test_write_text_file_reports_on_error(_mock_file, file_io):
    """
    Tests that write_text_file() fails gracefully, surfacing the failure through
    the error reporter instead of raising when the file cannot be written.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks the built-in open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    file_io.write_text_file(MagicMock(), "new contents")

    # The failure is reported to the user instead of raising
    file_io.report_error.assert_called_once()
