import PyPDF2, logging, os, tkinter
import PySimpleGUI as sg
from source.search import *
from source.invoice import *
from source.fio import *
from source.gui import InvoiceAppGUI

# Find all possible sales reps and payment terms, built from "Config" folder
sales_reps = build_dict_sales_reps()
payment_terms = build_list_payment_terms()


# process_invoice is the main function that processes the invoice pdf
# params: filename: str, the name of the file to be processed
# returns: N/A
# NOTE: Right now filename is actually the full file path to the invoice. This should either
# be changed or the variable should be renamed to filepath
def process_invoice(filename):

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
    invoice.populate_invoice(text, sales_reps, payment_terms)

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

            # "Total:subtotal" is the beginning of the end of the invoice
            if "Total:subtotal" in line:
                invoice = process_end_of_invoice(text, line, invoice)

    if __debug__:
        print_to_debug_file("Finished processing sales on current invoice!")

    # Calculate total from subtotal and sales tax
    invoice.calculate_total()

    # Print output to results.txt
    print_to_output_file(invoice)

    return invoice


# Entry Point
if __name__ == "__main__":

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s"
    )

    # If running in debug mode, reset debug.txt
    if __debug__:
        reset_debug_file()

    # Reset results.txt
    reset_output_file()

    # Create the Tkinter GUI application
    app = InvoiceAppGUI(process_callback=process_invoice)

    # Run the GUI application
    app.mainloop()
