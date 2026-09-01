from pathlib import Path
from unittest.mock import MagicMock, call, mock_open, patch

import pytest

from source.Invoice import Invoice
from source.InvoiceAppFileIO import InvoiceAppFileIO


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
@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_print_to_debug_file_appends(mock_debug_path, file_io):
    """
    Tests that print_to_debug_file() ensures the log directory exists, opens the
    debug log in append mode, and writes the contents with a trailing newline.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The method calls DEBUG_LOG_PATH.open(), not the built-in, so the mocked
    # constant carries the file handle
    mock_debug_path.open = mock_open()

    file_io.print_to_debug_file("some debug message")

    # The directory is ensured and the contents are appended
    mock_debug_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_debug_path.open.assert_called_once_with(mode="a")
    mock_debug_path.open().write.assert_called_once_with("some debug message\n")


@patch("source.InvoiceAppFileIO.DEBUG_LOG_PATH")
def test_print_to_debug_file_reports_on_error(mock_debug_path, file_io):
    """
    Tests that print_to_debug_file() fails gracefully, surfacing the failure
    through the error reporter instead of raising when the write fails.

    Args:
        mock_debug_path (unittest.mock.MagicMock): Mocks the DEBUG_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    mock_debug_path.open.side_effect = OSError("disk full")

    # No exception is raised, and the failure is reported to the user
    file_io.print_to_debug_file("some debug message")
    file_io.report_error.assert_called_once()


###############################################################################
###        Tests InvoiceAppFileIO -> print_invoice_to_output_file()         ###
###############################################################################
@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_print_invoice_to_output_file_overwrites_by_default(mock_results_path, file_io):
    """
    Tests that print_invoice_to_output_file() ensures the log directory exists,
    opens the results log in write mode (overwriting) by default, and writes the
    invoice's formatted string.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The method calls RESULTS_LOG_PATH.open(), not the built-in
    mock_results_path.open = mock_open()

    # Build a mock invoice whose formatted string is a known value
    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.to_formatted_string.return_value = "formatted invoice"

    file_io.print_invoice_to_output_file(mock_invoice)

    # The directory is ensured and the invoice is written in overwrite mode
    mock_results_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_results_path.open.assert_called_once_with(mode="w")
    mock_results_path.open().write.assert_called_once_with("formatted invoice")


@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_print_invoice_to_output_file_appends_when_requested(mock_results_path, file_io):
    """
    Tests that print_invoice_to_output_file() opens the results log in append mode
    when append_output is True and writes the invoice's formatted string.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The method calls RESULTS_LOG_PATH.open(), not the built-in
    mock_results_path.open = mock_open()

    # Build a mock invoice whose formatted string is a known value
    mock_invoice = MagicMock(spec=Invoice)
    mock_invoice.to_formatted_string.return_value = "formatted invoice"

    file_io.print_invoice_to_output_file(mock_invoice, append_output=True)

    # The invoice is written in append mode
    mock_results_path.open.assert_called_once_with(mode="a")
    mock_results_path.open().write.assert_called_once_with("formatted invoice")


@patch("source.InvoiceAppFileIO.RESULTS_LOG_PATH")
def test_print_invoice_to_output_file_reports_on_error(mock_results_path, file_io):
    """
    Tests that print_invoice_to_output_file() fails gracefully, surfacing the
    failure through the error reporter instead of raising when the write fails.

    Args:
        mock_results_path (unittest.mock.MagicMock): Mocks the RESULTS_LOG_PATH constant
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    mock_results_path.open.side_effect = OSError("disk full")

    mock_invoice = MagicMock(spec=Invoice)

    # No exception is raised, and the failure is reported to the user
    file_io.print_invoice_to_output_file(mock_invoice)
    file_io.report_error.assert_called_once()


###############################################################################
###              Tests InvoiceAppFileIO -> read_invoice_file()              ###
###############################################################################
@patch("source.InvoiceAppFileIO.pypdf.PdfReader")
def test_read_invoice_file_extracts_each_page(mock_reader, file_io):
    """
    Tests that read_invoice_file() returns the extracted text of each page in the
    PDF, in order.

    Args:
        mock_reader (unittest.mock.MagicMock): Mocks pypdf.PdfReader
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
    "source.InvoiceAppFileIO.pypdf.PdfReader",
    side_effect=OSError("file not found"),
)
def test_read_invoice_file_reports_and_returns_empty_on_error(mock_reader, file_io):
    """
    Tests that read_invoice_file() fails gracefully, surfacing the failure through
    the error reporter and returning an empty list when the PDF cannot be read.

    Args:
        mock_reader (unittest.mock.MagicMock): Mocks pypdf.PdfReader to raise
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    pages = file_io.read_invoice_file(Path("missing.pdf"))

    # No exception is raised, an empty list is returned, and the failure is reported
    assert pages == []
    file_io.report_error.assert_called_once()


###############################################################################
###              Tests InvoiceAppFileIO -> copy_invoice_file()              ###
###############################################################################
@patch("source.InvoiceAppFileIO.shutil.copy2")
@patch("source.InvoiceAppFileIO.INVOICES_DIR")
def test_copy_invoice_file_copies_new_file(mock_invoices_dir, mock_copy2, file_io):
    """
    Tests that copy_invoice_file() ensures the Invoices/ directory exists and
    copies the file when no same-named file is already present, returning
    "copied".

    Args:
        mock_invoices_dir (unittest.mock.MagicMock): Mocks the INVOICES_DIR constant
        mock_copy2 (unittest.mock.MagicMock): Mocks shutil.copy2
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # No same-named file exists in the destination yet
    destination = mock_invoices_dir.__truediv__.return_value
    destination.exists.return_value = False

    result = file_io.copy_invoice_file(Path("Downloads/invoice.pdf"))

    # The directory is ensured, the file is copied, and "copied" is returned
    mock_invoices_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_copy2.assert_called_once_with(Path("Downloads/invoice.pdf"), destination)
    assert result == "copied"


@patch("source.InvoiceAppFileIO.shutil.copy2")
@patch("source.InvoiceAppFileIO.INVOICES_DIR")
def test_copy_invoice_file_exists_without_overwrite(mock_invoices_dir, mock_copy2, file_io):
    """
    Tests that copy_invoice_file() does not overwrite an existing same-named file
    when overwrite is False, returning "exists" without copying.

    Args:
        mock_invoices_dir (unittest.mock.MagicMock): Mocks the INVOICES_DIR constant
        mock_copy2 (unittest.mock.MagicMock): Mocks shutil.copy2
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # A same-named file already exists in the destination
    destination = mock_invoices_dir.__truediv__.return_value
    destination.exists.return_value = True

    result = file_io.copy_invoice_file(Path("Downloads/invoice.pdf"))

    # No copy is made and "exists" is returned so the caller can confirm
    mock_copy2.assert_not_called()
    assert result == "exists"


@patch("source.InvoiceAppFileIO.shutil.copy2")
@patch("source.InvoiceAppFileIO.INVOICES_DIR")
def test_copy_invoice_file_overwrites_when_confirmed(mock_invoices_dir, mock_copy2, file_io):
    """
    Tests that copy_invoice_file() overwrites an existing same-named file when
    overwrite is True, copying the file and returning "copied".

    Args:
        mock_invoices_dir (unittest.mock.MagicMock): Mocks the INVOICES_DIR constant
        mock_copy2 (unittest.mock.MagicMock): Mocks shutil.copy2
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # A same-named file exists, but the caller has confirmed an overwrite
    destination = mock_invoices_dir.__truediv__.return_value
    destination.exists.return_value = True

    result = file_io.copy_invoice_file(Path("Downloads/invoice.pdf"), overwrite=True)

    # The file is copied over the existing one and "copied" is returned
    mock_copy2.assert_called_once_with(Path("Downloads/invoice.pdf"), destination)
    assert result == "copied"


@patch("source.InvoiceAppFileIO.shutil.copy2", side_effect=OSError("disk full"))
@patch("source.InvoiceAppFileIO.INVOICES_DIR")
def test_copy_invoice_file_reports_and_returns_error_on_failure(mock_invoices_dir, _mock_copy2, file_io):
    """
    Tests that copy_invoice_file() fails gracefully, surfacing the failure through
    the error reporter and returning "error" when the copy cannot be completed.

    Args:
        mock_invoices_dir (unittest.mock.MagicMock): Mocks the INVOICES_DIR constant
        _mock_copy2 (unittest.mock.MagicMock): Mocks shutil.copy2 to raise
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # The destination is clear, but the copy itself fails
    destination = mock_invoices_dir.__truediv__.return_value
    destination.exists.return_value = False

    result = file_io.copy_invoice_file(Path("Downloads/invoice.pdf"))

    # No exception is raised, "error" is returned, and the failure is reported
    assert result == "error"
    file_io.report_error.assert_called_once()


###############################################################################
###          Tests InvoiceAppFileIO -> parse_sales_reps_config()            ###
###############################################################################
@patch(
    "pathlib.Path.open",
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
        mock_file (unittest.mock.MagicMock): Mocks Path.open()
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
    mock_file.assert_called_once_with()


@patch(
    "pathlib.Path.open",
    new_callable=mock_open,
    read_data="",
)
def test_parse_sales_reps_config_empty_file(mock_file, file_io):
    """
    Tests that parse_sales_reps_config() returns an empty dictionary
    when the config file contains no entries.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks Path.open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Call parse_sales_reps_config() and save the return
    sales_reps = file_io.parse_sales_reps_config()

    # Expect an empty dictionary to be returned
    assert sales_reps == {}

    # Ensure the file was opened in reading mode
    mock_file.assert_called_once_with()


@patch("pathlib.Path.open", side_effect=OSError("file not found"))
def test_parse_sales_reps_config_reports_on_error(_mock_file, file_io):
    """
    Tests that parse_sales_reps_config() fails gracefully, surfacing the failure
    through the error reporter and returning an empty dictionary when the config
    file cannot be read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks Path.open() to raise
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
    "pathlib.Path.open",
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
        mock_file (unittest.mock.MagicMock): Mocks Path.open()
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
    mock_file.assert_called_once_with()


@patch(
    "pathlib.Path.open",
    new_callable=mock_open,
    read_data="",
)
def test_parse_payment_terms_config_empty_file(mock_file, file_io):
    """
    Tests that parse_payment_terms_config() returns an empty list
    when the config file contains no entries.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks Path.open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # Call parse_payment_terms_config() and save the return
    payment_terms = file_io.parse_payment_terms_config()

    # Expect an empty list to be returned
    assert payment_terms == []

    # Ensure the file was opened in reading mode
    mock_file.assert_called_once_with()


@patch("pathlib.Path.open", side_effect=OSError("file not found"))
def test_parse_payment_terms_config_reports_on_error(_mock_file, file_io):
    """
    Tests that parse_payment_terms_config() fails gracefully, surfacing the failure
    through the error reporter and returning an empty list when the config file
    cannot be read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks Path.open() to raise
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
    "pathlib.Path.open",
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
def test_parse_cost_criteria_file_calls_add_cost_criteria_field(mock_add_field, mock_file, file_io):
    """
    Tests that parse_cost_criteria_file() reads the file correctly and
    calls add_cost_criteria_field() with the expected arguments.

    Args:
        mock_add_field (unittest.mock.MagicMock): Mocks the add_cost_criteria_field method
        mock_file (unittest.mock.MagicMock): Mocks Path.open()
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
    mock_file.assert_called_once_with()


@patch("pathlib.Path.open", side_effect=OSError("file not found"))
def test_parse_cost_criteria_file_reports_on_error(_mock_file, file_io):
    """
    Tests that parse_cost_criteria_file() fails gracefully, surfacing the failure
    through the error reporter instead of raising when the config file cannot be
    read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks Path.open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # No exception is raised, and the failure is reported to the user
    file_io.parse_cost_criteria_file()
    file_io.report_error.assert_called_once()


@patch(
    "pathlib.Path.open",
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
        _mock_file (unittest.mock.MagicMock): Mocks Path.open()
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
    "pathlib.Path.open",
    new_callable=mock_open,
    read_data="line one\nline two\n",
)
def test_read_text_file_returns_contents(mock_file, file_io):
    """
    Tests that read_text_file() returns the full contents of the file.

    Args:
        mock_file (unittest.mock.MagicMock): Mocks Path.open()
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    file_path = Path("Configs/Sales_Reps.txt")
    contents = file_io.read_text_file(file_path)

    # The whole file is returned and it was opened for reading
    assert contents == "line one\nline two\n"
    mock_file.assert_called_once_with()


@patch("pathlib.Path.open", side_effect=OSError("file not found"))
def test_read_text_file_reports_on_error(_mock_file, file_io):
    """
    Tests that read_text_file() fails gracefully, surfacing the failure through
    the error reporter and returning an empty string when the file cannot be read.

    Args:
        _mock_file (unittest.mock.MagicMock): Mocks Path.open() to raise
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    contents = file_io.read_text_file(Path("Configs/Sales_Reps.txt"))

    # An empty string is returned and the failure is reported to the user
    assert contents == ""
    file_io.report_error.assert_called_once()


###############################################################################
###               Tests InvoiceAppFileIO -> write_text_file()               ###
###############################################################################
def test_write_text_file_writes_contents(file_io):
    """
    Tests that write_text_file() ensures the parent directory exists and writes
    the given contents to the file.

    Args:
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    # A mock path so the parent.mkdir and open calls can be asserted on
    mock_path = MagicMock()
    mock_path.open = mock_open()
    file_io.write_text_file(mock_path, "new contents")

    # The parent directory is ensured, then the file is opened for writing and written
    mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_path.open.assert_called_once_with(mode="w")
    mock_path.open().write.assert_called_once_with("new contents")


def test_write_text_file_reports_on_error(file_io):
    """
    Tests that write_text_file() fails gracefully, surfacing the failure through
    the error reporter instead of raising when the file cannot be written.

    Args:
        file_io (pytest.fixture): Test fixture for InvoiceAppFileIO
    """

    mock_path = MagicMock()
    mock_path.open.side_effect = OSError("permission denied")
    file_io.write_text_file(mock_path, "new contents")

    # The failure is reported to the user instead of raising
    file_io.report_error.assert_called_once()
