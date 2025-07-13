# Import necessary classes from modules
from .InvoiceAppDisplay import InvoiceAppDisplay
from .InvoiceAppFileIO import InvoiceAppFileIO
from .InvoiceProcessor import InvoiceProcessor
from .Invoice import Invoice

# General TODO: Remove params or returns from function header comments if there are none
# General TODO: Check all functions in classes and make sure they have self if needed
#               Some functions may not need self if they are just used internally
#               If they are used externally, they should have self
# General TODO: Add lots of ##### above and below function headers? Or block comments?


# InvoiceAppController class to drive logic for processing invoice PDFs.
class InvoiceAppController:

    # __init__ Constructor
    # returns: Created InvoiceAppController object
    def __init__(self):

        # Define the filepath for debug log files
        self.debug_log_path = "logs/debug.txt"

        # Define the filepath for saved results log files
        self.results_log_path = "logs/results.txt"

        # Define the filepath for Invoices to be processed
        self.invoices_path = "Invoices"

        # Define the filepath for the payment terms config file
        self.payment_terms_path = "Configs/paymentTerms.txt"

        # Define the filepath for the sales reps config file
        self.sales_reps_path = "Configs/salesReps.txt"

        # Create File IO Controller, provide it with all necessary file paths
        self.file_io_controller = InvoiceAppFileIO(
            debug_filepath=self.debug_log_path,
            results_filepath=self.results_log_path,
            invoices_filepath=self.invoices_path,
            payment_terms_filepath=self.payment_terms_path,
            sales_reps_filepath=self.sales_reps_path,
        )

        # Create InvoiceProcessor
        self.invoice_processor = InvoiceProcessor()

        # TODO: Since this is the Invoice App "Controller" it should tell the display how to create itself. Move default values out of the
        # InvoiceAppDisplay constructor and move them into here
        self.display = InvoiceAppDisplay(
            process_callback=self.handle_process_invoice
        )  # GUI display to drive selecting and processing invoices

        # Build payment terms dictionary containing sales rep name codes that could appear on an invoice
        self.payment_terms = self.file_io_controller.build_payment_terms_list()

        # Build sales_rep dictionary containing all possible payment terms that could appear on an invoice
        self.sales_reps = self.file_io_controller.build_sales_reps_dict()

    # Start the application by entering the tkinter main GUI loop
    def start_application(self):

        # Reset text files before starting the application
        if __debug__:
            self.file_io_controller.reset_debug_file()

        self.file_io_controller.reset_results_file()

        self.display.mainloop()  # Start the GUI application

    # handle_process_invoice handles the controller side of the invoice processing
    # param: invoice_filepath: str, the filepath of the invoice PDF to be processed
    def handle_process_invoice(self, invoice_filepath):

        invoice = Invoice()

        # Command the File IO Controller to read in the invoice
        invoice.page_contents = self.file_io_controller.read_invoice_file(
            invoice_filepath=invoice_filepath
        )

        # If there are no pages in the invoice, return early
        if not invoice.page_contents or invoice.page_contents[0] is None:
            # TODO: Tell the GUI to display a popup error message.
            # Maybe popping up the error message should be a generic thing, that can
            # be called from anywhere, so can do self.display.show_error_popup(message)
            return

        # Print results of reading invoice to debug.txt if in debug mode
        self.file_io_controller.print_to_debug_file(
            f"Processing invoice: {invoice_filepath} with {len(invoice.page_contents)} pages."
        )

        # Populate other initial fields of the invoice from the first page of the PDF
        self.invoice_processor.populate_invoice(
            invoice, self.sales_reps, self.payment_terms
        )

        # Forward call to the Invoice Processor
        self.invoice_processor.process_invoice(invoice=invoice)

        # Display the calculated totals in the GUI
        self.display.display_invoice_output(invoice=invoice)
        
        # Print calculated invoice output to results.txt
        self.file_io_controller.print_invoice_to_output_file(invoice)
