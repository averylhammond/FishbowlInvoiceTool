# Import necessary classes from modules
from source.Invoice import Invoice
from source.InvoiceAppGUI import InvoiceAppDisplay

# TODO: Eventually want to move this to a separate module to do PDF processing
import PyPDF2

# TODO: Need to figure out what to do with these, should they be integrated into the InvoiceProcessor class?
from source.fio import *

# TODO: What to do with this? Could be in this file but would be best to separate it out
from source.search import *


# InvoiceProcessor class to drive logic for processing invoice PDFs.
class InvoiceProcessor:

    def __init__(self):

        # Build payment terms dictionary with the filepath to config file containing sales rep name codes that could appear on an invoice
        self.payment_terms = build_list_payment_terms("Configs/paymentTerms.txt")

        # Build sales_rep dictionary with the filepath to config file containing all possible payment terms that could appear on an invoice
        self.sales_reps = build_dict_sales_reps("Configs/salesReps.txt")

        self.display = InvoiceAppDisplay(
            process_callback=self.process_invoice
        )  # GUI display to drive selecting and processing invoices

    def start(self):
        self.reset_text_files()
        self.display.mainloop()  # Start the GUI application

    def reset_text_files(self):
        # If running in debug mode, reset debug.txt
        if __debug__:
            reset_debug_file()

        # Reset results.txt
        reset_output_file()

    # process_invoice is the main function that processes the invoice pdf
    # params: filename: str, the name of the file to be processed
    # returns: N/A
    # NOTE: Right now filename is actually the full file path to the invoice. This should either
    # be changed or the variable should be renamed to filepath
    def process_invoice(self, filename):

        # Read text from input PDF
        pdf = PyPDF2.PdfReader(filename)

        # Get Number of Pages
        num_pages = len(pdf.pages)

        if __debug__:
            print_to_debug_file(f"\nProcessing file: {filename}")
            print_to_debug_file(f"Number of Pages in invoice: {num_pages}")

        # Process First Page
        curr_page = pdf.pages[0]
        text = curr_page.extract_text()

        # Create Invoice object and populate initial fields
        invoice = Invoice()
        invoice.populate_invoice(text, self.sales_reps, self.payment_terms)

        # Keep track of next expected payment line number
        next_line_num = 1

        # Loop through each page to read purchase table
        for i in range(1, num_pages + 1):

            if __debug__:
                print_to_debug_file(f"Processing sales on page {i}")

            # If not on first page, extract text from new page
            if i > 1:
                curr_page = pdf.pages[i - 1]
                text = curr_page.extract_text()

            # At this point, can disregard everything before the purchase table
            # Trim off everything before purchase table (before the line Ordered Total Price)
            if len(text[(text.find("Ordered Total Price")) :]) > 1:
                text = text[(text.find("Ordered Total Price")) :]

            # Loop through each line in the table. Some table entries may have multiple lines that need
            # to be processed
            for line in text.splitlines():

                # Check if at beginning of the line in the table. If so, process this payment item
                if line.startswith(f"{next_line_num} "):
                    invoice = process_payment_line(text, line, invoice, next_line_num)
                    next_line_num += 1  # Update nextLineNum

                # "Total:Subtotal" is the beginning of the end of the invoice
                if "Total:Subtotal" in line:
                    invoice, diff = process_end_of_invoice(text, line, invoice)

        if __debug__:
            print_to_debug_file("Finished processing sales on current invoice!")

        # Calculate total from subtotal and sales tax
        invoice.calculate_total()

        # Print output to results.txt
        print_to_output_file(invoice)

        return invoice, diff
