import pytest
from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal

from source.InvoiceAppController import InvoiceAppController


###############################################################################
###                   InvoiceAppController -> Test Fixture                  ###
###############################################################################
@pytest.fixture
def controller():
    """
    Builds an InvoiceAppController with every collaborator it constructs replaced
    by a mock, so the controller is exercised in complete isolation (no real file
    I/O, no tkinter window, no PDF parsing).

    Returns:
        types.SimpleNamespace: Holds the constructed controller (`controller`) and
            the mocked collaborator instances (`arg_provider`, `file_io`,
            `processor`, `display`) plus the patched `Invoice` class so individual
            tests can configure return values and assert calls.
    """

    with (
        patch("source.InvoiceAppController.ArgumentProvider") as mock_arg_provider_cls,
        patch("source.InvoiceAppController.InvoiceAppFileIO") as mock_file_io_cls,
        patch("source.InvoiceAppController.InvoiceProcessor") as mock_processor_cls,
        patch("source.InvoiceAppController.InvoiceAppDisplay") as mock_display_cls,
        patch("source.InvoiceAppController.Invoice") as mock_invoice_cls,
    ):

        # Grab the instance each patched class returns when constructed
        mock_arg_provider = mock_arg_provider_cls.return_value
        mock_file_io = mock_file_io_cls.return_value
        mock_processor = mock_processor_cls.return_value
        mock_display = mock_display_cls.return_value

        # Provide the criteria attributes the controller reads off file_io while
        # wiring up the InvoiceProcessor during construction
        mock_file_io.labor_criteria = ["LABOR"]
        mock_file_io.labor_exclusions = ["NO-LABOR"]
        mock_file_io.shipping_criteria = ["SHIPPING"]

        # Config parsing return values the controller stores during construction
        mock_file_io.parse_payment_terms_config.return_value = ["Net 30"]
        mock_file_io.parse_sales_reps_config.return_value = {"REP1": "Rep Name"}

        # Default to GUI (non integration-test) mode
        mock_arg_provider.integration_test_mode = False

        built_controller = InvoiceAppController()

        yield SimpleNamespace(
            controller=built_controller,
            arg_provider_cls=mock_arg_provider_cls,
            arg_provider=mock_arg_provider,
            file_io_cls=mock_file_io_cls,
            file_io=mock_file_io,
            processor_cls=mock_processor_cls,
            processor=mock_processor,
            display_cls=mock_display_cls,
            display=mock_display,
            invoice_cls=mock_invoice_cls,
            invoice=mock_invoice_cls.return_value,
        )


###############################################################################
###               Tests InvoiceAppController -> __init__()                  ###
###############################################################################
def test_init_constructs_and_wires_collaborators(controller):
    """
    Verifies that __init__ constructs each collaborator and wires the
    InvoiceProcessor and InvoiceAppDisplay with the expected dependencies.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Each collaborator should have been constructed exactly once
    controller.arg_provider_cls.assert_called_once_with()
    controller.file_io_cls.assert_called_once_with()

    # The processor is wired with the file_io controller and the criteria pulled
    # off of it
    controller.processor_cls.assert_called_once_with(
        file_io_controller=controller.file_io,
        labor_criteria=["LABOR"],
        labor_exclusions=["NO-LABOR"],
        shipping_criteria=["SHIPPING"],
    )

    # The display is wired with the controller's process callback
    controller.display_cls.assert_called_once_with(
        title="Invoice Processor",
        window_resolution="750x750",
        process_callback=controller.controller.handle_process_invoice,
    )


def test_init_loads_config_files(controller):
    """
    Verifies that __init__ loads the cost criteria, payment terms, and sales reps
    config files and stores the parsed results on the controller.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Cost criteria are parsed into the file_io controller during construction
    controller.file_io.parse_cost_criteria_file.assert_called_once_with()

    # Payment terms and sales reps are parsed and stored on the controller
    controller.file_io.parse_payment_terms_config.assert_called_once_with()
    controller.file_io.parse_sales_reps_config.assert_called_once_with()
    assert controller.controller.payment_terms == ["Net 30"]
    assert controller.controller.sales_reps == {"REP1": "Rep Name"}


def test_init_wires_error_reporter(controller):
    """
    Verifies that __init__ wires the display's error popup into the file IO
    controller as its error reporter, so file I/O failures surface to the user.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The file IO controller reports errors through the display's popup
    assert controller.file_io.report_error is controller.display.show_error_popup


###############################################################################
###            Tests InvoiceAppController -> start_application()            ###
###############################################################################
def test_start_application_resets_files_and_starts_gui(controller):
    """
    Verifies that start_application resets the log files and enters the GUI main
    loop when not in integration test mode.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.arg_provider.integration_test_mode = False

    controller.controller.start_application()

    # Log files are reset before the application starts
    controller.file_io.reset_debug_file.assert_called_once_with()
    controller.file_io.reset_results_file.assert_called_once_with()

    # The GUI main loop is started, and invoices are not processed directly
    controller.display.mainloop.assert_called_once_with()
    controller.display.handle_process_all_invoices.assert_not_called()


def test_start_application_integration_test_mode_processes_all(controller):
    """
    Verifies that start_application processes all invoices directly (without the
    GUI loop) when running in integration test mode.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.arg_provider.integration_test_mode = True

    controller.controller.start_application()

    # All invoices are processed directly, and the GUI loop is never entered
    controller.display.handle_process_all_invoices.assert_called_once_with()
    controller.display.mainloop.assert_not_called()


###############################################################################
###          Tests InvoiceAppController -> handle_process_invoice()         ###
###############################################################################
def test_handle_process_invoice_no_pages_shows_error_and_returns(controller):
    """
    Verifies that handle_process_invoice shows an error popup and returns early
    when the invoice PDF has no pages.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The PDF read returns no pages
    controller.file_io.read_invoice_file.return_value = []

    controller.controller.handle_process_invoice(
        invoice_filepath="missing.pdf", append_output=False
    )

    # An error popup is shown and processing stops before populating the invoice
    controller.display.show_error_popup.assert_called_once()
    controller.processor.populate_invoice.assert_not_called()
    controller.processor.process_invoice.assert_not_called()


def test_handle_process_invoice_first_page_none_shows_error_and_returns(controller):
    """
    Verifies that handle_process_invoice shows an error popup and returns early
    when the first page of the invoice PDF is None.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The PDF read returns a page list whose first page failed to parse
    controller.file_io.read_invoice_file.return_value = [None]

    controller.controller.handle_process_invoice(
        invoice_filepath="bad.pdf", append_output=False
    )

    # An error popup is shown and processing stops before populating the invoice
    controller.display.show_error_popup.assert_called_once()
    controller.processor.populate_invoice.assert_not_called()


def test_handle_process_invoice_full_flow_totals_match(controller):
    """
    Verifies the full happy-path flow: when the calculated total matches the
    listed total, the invoice is populated, processed, displayed, and written to
    the output file with no mismatch popup.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # A single valid page is read, and the totals match
    controller.file_io.read_invoice_file.return_value = ["page one text"]
    controller.invoice.total = Decimal("10.00")
    controller.invoice.listed_total = Decimal("10.00")

    controller.controller.handle_process_invoice(
        invoice_filepath="invoice.pdf", append_output=True
    )

    # The processor is asked to populate and process the invoice
    controller.processor.populate_invoice.assert_called_once_with(
        invoice=controller.invoice,
        sales_reps=controller.controller.sales_reps,
        payment_terms=controller.controller.payment_terms,
    )
    controller.processor.process_invoice.assert_called_once_with(
        invoice=controller.invoice
    )

    # The output is displayed and written, honoring the append_output flag
    controller.display.display_invoice_output.assert_called_once_with(
        invoice=controller.invoice, append_output=True
    )
    controller.file_io.print_invoice_to_output_file.assert_called_once_with(
        invoice=controller.invoice, append_output=True
    )

    # No mismatch popup is shown when the totals match
    controller.display.show_error_popup.assert_not_called()


def test_handle_process_invoice_total_mismatch_shows_popup(controller):
    """
    Verifies that handle_process_invoice shows a mismatch error popup when the
    calculated total does not match the listed total, while still writing output.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # A single valid page is read, but the totals disagree
    controller.file_io.read_invoice_file.return_value = ["page one text"]
    controller.invoice.total = Decimal("10.00")
    controller.invoice.listed_total = Decimal("9.99")

    controller.controller.handle_process_invoice(
        invoice_filepath="invoice.pdf", append_output=False
    )

    # A mismatch popup is shown, and the output is still written
    controller.display.show_error_popup.assert_called_once()
    controller.file_io.print_invoice_to_output_file.assert_called_once_with(
        invoice=controller.invoice, append_output=False
    )
