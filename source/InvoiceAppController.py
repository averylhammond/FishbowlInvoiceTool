# Import necessary classes from modules
from source.InvoiceAppDisplay import InvoiceAppDisplay
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.InvoiceProcessor import InvoiceProcessor
from source.Invoice import Invoice


# TODO: Rename payment terms and sales reps config files
# TODO: Move the config files to a private repo? Should that information be public?
# TODO: Move the criteria for different costs to the config files? Private?


# InvoiceAppController class to drive logic for processing invoice PDFs.
class InvoiceAppController:

    def __init__(self):
        """
        Initializes the InvoiceAppController object

        This includes specifying the file paths for logs, invoices, config files, and initializing
        the File IO Controller, Invoice Processor, and GUI Display.

        Note that all defined filepaths are relative to the executable's current working directory.
        """

        # Define the filepath for the debug log
        self.debug_log_path = "logs/debug.txt"

        # Define the filepath for the saved results log
        self.results_log_path = "logs/results.txt"

        # Define the filepath for Invoices to be processed
        self.invoices_path = "Invoices"

        # Define the filepath for the payment terms config file
        self.payment_terms_path = "Configs/Payment_Terms.txt"

        # Define the filepath for the sales reps config file
        self.sales_reps_path = "Configs/Sales_Reps.txt"

        # Create File IO Controller, provide it with all necessary file paths
        self.file_io_controller = InvoiceAppFileIO(
            debug_filepath=self.debug_log_path,
            results_filepath=self.results_log_path,
            invoices_filepath=self.invoices_path,
            payment_terms_filepath=self.payment_terms_path,
            sales_reps_filepath=self.sales_reps_path,
        )

        # Create InvoiceProcessor, provide it with the File IO Controller and criteria for processing invoices
        self.invoice_processor = InvoiceProcessor(
            file_io_controller=self.file_io_controller,
            labor_criteria=["MF/", "MD/"],
            labor_exclusions=["MF/RHR", "MF/LHR", "MD/RHR", "MD/LHR"],
            shipping_criteria=["DELIVERY", "UPS GROUND", "FREIGHT OUT"],
        )

        # Create the InvoiceAppDisplay GUI, provide it with callback function to process invoices
        self.display = InvoiceAppDisplay(
            title="Invoice Processor",
            window_resolution="750x750",
            process_callback=self.handle_process_invoice,
            invoices_dir=self.invoices_path,
        )

        # Build payment terms dictionary containing all possible sales rep name codes that could appear on an invoice
        self.payment_terms = self.file_io_controller.build_payment_terms_list()

        # Build sales_rep dictionary containing all possible payment terms that could appear on an invoice
        self.sales_reps = self.file_io_controller.build_sales_reps_dict()

    def start_application(self):
        """
        Starts the application by entering the tkinter main GUI loop
        """

        # Reset text files before starting the application
        if __debug__:
            self.file_io_controller.reset_debug_file()

        self.file_io_controller.reset_results_file()

        # Start the GUI application
        self.display.mainloop()

    def handle_process_invoice(
        self, invoice_filepath: str, append_output: bool
    ):
        """
        Directs components to process the invoice located at invoice_filepath

        Args:
            invoice_filepath (str): The filepath of the invoice PDF to be processed.
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
                error_message="No pages were found in the invoice PDF located at {invoice_filepath}.",
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
