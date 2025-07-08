# Import necessary classes from modules
from Invoice import Invoice
from InvoiceAppDisplay import InvoiceAppDisplay
from InvoiceAppFileIO import InvoiceAppFileIO
from InvoiceProcessor import InvoiceProcessor

# General TODO: Remove params or returns from function header comments if there are none
# General TODO: Check all functions in classes and make sure they have self if needed
#               Some functions may not need self if they are just used internally
#               If they are used externally, they should have self


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

        # Build payment terms dictionary containing sales rep name codes that could appear on an invoice
        self.payment_terms = self.file_io_controller.build_payment_terms_list()

        # Build sales_rep dictionary containing all possible payment terms that could appear on an invoice
        self.sales_reps = self.file_io_controller.build_sales_reps_dict()

        # TODO: Since this is the Invoice App "Controller" it should tell the display how to create itself. Move default values out of the
        # InvoiceAppDisplay constructor and move them into here
        self.display = InvoiceAppDisplay(
            process_callback=self.process_invoice
        )  # GUI display to drive selecting and processing invoices

    # Start the application by entering the tkinter main GUI loop
    def start_application(self):

        # Reset text files before starting the application
        if __debug__:
            self.file_io_controller.reset_debug_file()

        self.file_io_controller.reset_results_file()

        self.display.mainloop()  # Start the GUI application
