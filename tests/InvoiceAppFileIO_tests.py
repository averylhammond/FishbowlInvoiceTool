import pytest
from unittest.mock import patch, mock_open, call

from source.InvoiceAppFileIO import *


###############################################################################
###                      InvoiceAppFileIO -> Test Fixture                   ###
###############################################################################
@pytest.fixture
def file_io():
    """
    Test fixture to set up an InvoiceAppFileIO object for testing to maximize
    code reuse
    """

    return InvoiceAppFileIO(
        debug_filepath="debug.txt",
        results_filepath="results.txt",
        invoices_filepath="invoices/",
        payment_terms_filepath="payment_terms.txt",
        sales_reps_filepath="sales_reps.txt",
        cost_criteria_filepath="cost_criteria.txt",
    )


###############################################################################
###              Tests InvoiceAppFileIO -> reset_debug_file()               ###
###############################################################################
@patch("os.path.dirname", return_value="debug.txt")
@patch("os.path.exists", return_value=False)
def test_reset_debug_file_path_doesnt_exist(
    _mock_os_exists, _mock_os_dirname, file_io
):
    """
    Tests that the function reset_debug_file() will raise an exception if
    the debug.txt file path does not exist where the InvoiceAppFileIO object
    is told that it will

    Args:
        _mock_os_exists (unittest.mock.MagicMock): mock os.path.exists to return false
        _mock_os_dirname (unittest.mock.MagicMock): mock os.path.dirname to return the filename
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Call reset_debug_file(), expecting an exception to be raised
    with pytest.raises(FileNotFoundError) as exception:
        file_io.reset_debug_file()

    assert "Debug file directory debug.txt does not exist" in str(exception)


@patch("os.remove")
@patch("os.path.isfile", return_value=True)
@patch("os.path.dirname", return_value="debug.txt")
@patch("os.path.exists", return_value=True)
def test_reset_debug_file_file_exists(
    _mock_os_exists, _mock_os_dirname, _mock_os_isfile, mock_os_remove, file_io
):
    """
    Tests that the function reset_debug_file() will delete the debug log file if it exists

    Args:
        _mock_os_exists (unittest.mock.MagicMock): mock os.path.exists to return false
        _mock_os_dirname (unittest.mock.MagicMock): mock os.path.dirname to return the filename
        _mock_os_isfile (unittest.mock.MagicMock): mock os.path.isfile to return true
        mock_os_remove (unittest.mock.MagicMock): mock os.remove to check the call count
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Call reset_debug_file(), expecting os.remove() to be called once
    file_io.reset_debug_file()
    mock_os_remove.assert_called_once_with(file_io.debug_filepath)


@patch("os.remove")
@patch("os.path.isfile", return_value=False)
@patch("os.path.dirname", return_value="debug.txt")
@patch("os.path.exists", return_value=True)
def test_reset_debug_file_file_doesnt_exist(
    _mock_os_exists, _mock_os_dirname, _mock_os_isfile, mock_os_remove, file_io
):
    """
    Tests that the function reset_debug_file() will not call os.remove() to delete
    the debug log file if it does not exist

    Args:
        _mock_os_exists (unittest.mock.MagicMock): mock os.path.exists to return false
        _mock_os_dirname (unittest.mock.MagicMock): mock os.path.dirname to return the filename
        _mock_os_isfile (unittest.mock.MagicMock): mock os.path.isfile to return true
        mock_os_remove (unittest.mock.MagicMock): mock os.remove to check the call count
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Call reset_debug_file(), expecting os.remove() to not be called since the
    # file doesn't exist
    file_io.reset_debug_file()
    mock_os_remove.assert_not_called()


###############################################################################
###              Tests InvoiceAppFileIO -> reset_results_file()             ###
###############################################################################
@patch("os.path.dirname", return_value="results.txt")
@patch("os.path.exists", return_value=False)
def test_reset_results_file_path_doesnt_exist(
    _mock_os_exists, _mock_os_dirname, file_io
):
    """
    Tests that the function reset_results_file() will raise an exception if
    the results.txt file path does not exist where the InvoiceAppFileIO object
    is told that it will

    Args:
        _mock_os_exists (unittest.mock.MagicMock): mock os.path.exists to return false
        _mock_os_dirname (unittest.mock.MagicMock): mock os.path.dirname to return the filename
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Call reset_results_file(), expecting an exception to be raised
    with pytest.raises(FileNotFoundError) as exception:
        file_io.reset_results_file()

    assert "Results file path results.txt does not exist" in str(exception)


@patch("os.remove")
@patch("os.path.isfile", return_value=True)
@patch("os.path.dirname", return_value="results.txt")
@patch("os.path.exists", return_value=True)
def test_reset_results_file_file_exists(
    _mock_os_exists, _mock_os_dirname, _mock_os_isfile, mock_os_remove, file_io
):
    """
    Tests that the function reset_results_file() will delete the results log file if it exists

    Args:
        _mock_os_exists (unittest.mock.MagicMock): mock os.path.exists to return false
        _mock_os_dirname (unittest.mock.MagicMock): mock os.path.dirname to return the filename
        _mock_os_isfile (unittest.mock.MagicMock): mock os.path.isfile to return true
        mock_os_remove (unittest.mock.MagicMock): mock os.remove to check the call count
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Call reset_results_file(), expecting os.remove() to be called once
    file_io.reset_results_file()
    mock_os_remove.assert_called_once_with(file_io.results_filepath)


@patch("os.remove")
@patch("os.path.isfile", return_value=False)
@patch("os.path.dirname", return_value="results.txt")
@patch("os.path.exists", return_value=True)
def test_reset_results_file_file_doesnt_exist(
    _mock_os_exists, _mock_os_dirname, _mock_os_isfile, mock_os_remove, file_io
):
    """
    Tests that the function reset_results_file() will not call os.remove() to delete
    the results log file if it does not exist

    Args:
        _mock_os_exists (unittest.mock.MagicMock): mock os.path.exists to return false
        _mock_os_dirname (unittest.mock.MagicMock): mock os.path.dirname to return the filename
        _mock_os_isfile (unittest.mock.MagicMock): mock os.path.isfile to return true
        mock_os_remove (unittest.mock.MagicMock): mock os.remove to check the call count
        file_io (pytest.fixture): Test fixture to create the InvoiceAppFileIO object
    """

    # Call reset_results_file(), expecting os.remove() to not be called since the
    # file doesn't exist
    file_io.reset_results_file()
    mock_os_remove.assert_not_called()


###############################################################################
###              Tests InvoiceAppFileIO -> read_invoice_file()              ###
###############################################################################

"""
Opting to not write unit tests for this function since PyPDF2 will be replaced soon
"""


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
    mock_file.assert_called_once_with(
        file=file_io.sales_reps_filepath, mode="r"
    )


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
    mock_file.assert_called_once_with(
        file=file_io.sales_reps_filepath, mode="r"
    )


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
    mock_file.assert_called_once_with(
        file=file_io.payment_terms_filepath, mode="r"
    )


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
    mock_file.assert_called_once_with(
        file=file_io.payment_terms_filepath, mode="r"
    )


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
    file_io.add_cost_criteria_field(
        "SHIPPING CRITERIA", "Shipping criterion 1"
    )

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
    mock_file.assert_called_once_with(file="cost_criteria.txt", mode="r")
