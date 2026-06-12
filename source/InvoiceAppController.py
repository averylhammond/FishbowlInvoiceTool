# Import necessary classes from modules
from pathlib import Path

from source.InvoiceAppDisplay import InvoiceAppDisplay
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.InvoiceProcessor import InvoiceProcessor
from source.ArgumentProvider import ArgumentProvider
from source.Invoice import Invoice

# TODO: The GUI title and window resolution below are still hardcoded; move these
#       into named constants (e.g. alongside the font/theme settings) as well
# TODO: See if there is a good logging method to add for debugging


# InvoiceAppController class to drive logic for processing invoice PDFs.
class InvoiceAppController:

    ###########################################################################
    ###                 InvoiceAppController -> __init__()                  ###
    ###########################################################################
    def __init__(self):
        """
        Initializes the InvoiceAppController object

        This includes initializing the File IO Controller, Invoice Processor,
        and GUI Display
        """

        # Argument provider to check for integration test mode
        self.argument_provider = ArgumentProvider()

        # Create File IO Controller, which reads its file paths from source.constants
        self.file_io_controller = InvoiceAppFileIO()

        # Create InvoiceProcessor, provide it with the File IO Controller and criteria for processing invoices
        self.invoice_processor = InvoiceProcessor(
            file_io_controller=self.file_io_controller,
            labor_criteria=self.file_io_controller.labor_criteria,
            labor_exclusions=self.file_io_controller.labor_exclusions,
            shipping_criteria=self.file_io_controller.shipping_criteria,
        )

        # Create the InvoiceAppDisplay GUI, provide it with the callback function to process invoices.
        self.display = InvoiceAppDisplay(
            title="Invoice Processor",
            window_resolution="750x750",
            process_callback=self.handle_process_invoice,
        )

        # Wire the GUI's error popup into the File IO Controller so file I/O failures
        # surface to the user without coupling file I/O to the GUI. This must happen
        # before the config files are parsed below so parse failures can be reported.
        self.file_io_controller.report_error = self.display.show_error_popup

        # Use the File IO Controller to read in the criteria/exclusions for each cost section
        self.file_io_controller.parse_cost_criteria_file()

        # Build payment terms dictionary containing all possible sales rep name codes that could appear on an invoice
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

        # Build sales_rep dictionary containing all possible payment terms that could appear on an invoice
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()

    ###########################################################################
    ###             InvoiceAppController -> start_application()             ###
    ###########################################################################
    def start_application(self):
        """
        Starts the application by entering the tkinter main GUI loop

        Note: If the application is running in integration test mode, the GUI loop is not started,
        and the application is instead directed to process all invoices directly.
        """

        # Reset text files before starting the application
        if __debug__:
            self.file_io_controller.reset_debug_file()

        self.file_io_controller.reset_results_file()

        if self.argument_provider.integration_test_mode:
            # If in integration test mode, process all invoices directly without starting the GUI
            self.display.handle_process_all_invoices()
        else:
            # Else, normally start the GUI application
            self.display.mainloop()

    ###########################################################################
    ###          InvoiceAppController -> handle_process_invoice()           ###
    ###########################################################################
    def handle_process_invoice(self, invoice_filepath: Path, append_output: bool):
        """
        Directs components to process the invoice located at invoice_filepath

        Args:
            invoice_filepath (Path): The filepath of the invoice PDF to be processed.
            append_output (bool): Whether to append the Invoice outputs to any existing outputs.
                                    True: append to existing results.txt and output box
                                    False: overwrite existing results.txt and output box
        """

        invoice = Invoice()

        # Command the File IO Controller to read in the invoice located at invoice_filepath
        invoice.page_contents = self.file_io_controller.read_invoice_file(
            invoice_filepath=invoice_filepath
        )

        # If there are no pages in the invoice, show an error and return early
        if not invoice.page_contents or invoice.page_contents[0] is None:
            self.display.show_error_popup(
                error_title="Error",
                error_message=f"No pages were found in the invoice PDF located at {invoice_filepath}.",
            )
            return

        # Print results of reading invoice to debug.txt if in debug mode
        self.file_io_controller.print_to_debug_file(
            f"Processing invoice: {invoice_filepath} with {len(invoice.page_contents)} pages."
        )

        # Populate other initial fields of the invoice from the first page of the PDF
        self.invoice_processor.populate_invoice(
            invoice=invoice,
            sales_reps=self.sales_reps,
            payment_terms=self.payment_terms,
        )

        # Forward call to the Invoice Processor
        self.invoice_processor.process_invoice(invoice=invoice)

        # Display the calculated totals in the GUI
        self.display.display_invoice_output(
            invoice=invoice, append_output=append_output
        )

        # Invoices generated by Fishbowl are known to have rounding errors, likely due to floating point precision issues, so
        # we need to account for that and let the user know that the generated total may not match the listed total on the invoice.
        # This is done by displaying an error popup window
        if invoice.total != invoice.listed_total:
            self.display.show_error_popup(
                error_title="Calculated Total Mismatch",
                error_message=f"The calculated total of ${invoice.total} does not match the listed total of ${invoice.listed_total} for invoice {invoice.order_number}.",
            )

        # Print calculated invoice output to results.txt
        self.file_io_controller.print_invoice_to_output_file(
            invoice=invoice, append_output=append_output
        )

        # Print completion notice to debug.txt if in debug mode
        self.file_io_controller.print_to_debug_file(
            contents=f"Processed all sales for invoice: {invoice_filepath}\n"
        )
