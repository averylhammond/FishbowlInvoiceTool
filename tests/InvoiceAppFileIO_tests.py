import pytest
from unittest.mock import patch

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
