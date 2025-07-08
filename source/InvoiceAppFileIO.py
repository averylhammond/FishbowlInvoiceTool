import os, PyPDF2
from .Invoice import Invoice


# InvoiceAppFileIO class to handle all file input/output operations
class InvoiceAppFileIO:

    # __init__ Constructor
    # param: results_filepath: str, the desired filepath to maintain the results.txt file
    # param: debug_filepath: str, the desired filepath to maintain the debug.txt file
    # param: invoices_filepath: str, the desired filepath to expect invoice PDFs to be located
    # param: payment_terms_filepath: str, the desired filepath to expect the payment terms config file
    # param: sales_reps_filepath: str, the desired filepath to expect the sales reps config file
    # returns: Created InvoiceAppFileIO object
    def __init__(
        self,
        debug_filepath,
        results_filepath,
        invoices_filepath,
        payment_terms_filepath,
        sales_reps_filepath,
    ):

        # Initialize file paths
        self.debug_filepath = debug_filepath
        self.results_filepath = results_filepath
        self.invoices_filepath = invoices_filepath
        self.payment_terms_filepath = payment_terms_filepath
        self.sales_reps_filepath = sales_reps_filepath

    # reset_debug_file deletes the debug.txt that was created from the previous program execution
    # note: This function does nothing in the release configuration
    def reset_debug_file(self):

        # If in release configuration, do nothing
        if not __debug__:
            return

        # Check to make sure the filepath exists
        if not os.path.exists(os.path.dirname(self.debug_filepath)):
            raise FileNotFoundError(
                f"Debug file directory {os.path.dirname(self.debug_filepath)} does not exist."
            )

        # If the file already exists, delete it
        if os.path.isfile(self.debug_filepath):
            os.remove(self.debug_filepath)

    # reset_results_file deletes results.txt that was created from the previous program execution
    # note: This function does nothing in the release configuration
    def reset_results_file(self):

        # Check to make sure the filepath exists
        if not os.path.exists(os.path.dirname(self.debug_filepath)):
            raise FileNotFoundError(
                f"Results file path {os.path.dirname(self.results_filepath)} does not exist."
            )

        # If the file already exists, delete it
        if os.path.isfile(self.results_filepath):
            os.remove(self.results_filepath)

    # print_to_debug_file writes the str contents to debug.txt
    # param: contents: str, the contents to be written to file
    # note: This function does nothing in the release configuration
    def print_to_debug_file(self, contents):

        # If in release configuration, do nothing
        if not __debug__:
            return

        # If debug.txt already exists, append to it, otherwise write from beginning
        if os.path.exists(os.path.dirname(self.debug_filepath)):
            write_or_append = "a"
        else:
            write_or_append = "w"

        # Write contents to file
        with open(self.debug_filepath, write_or_append) as f:
            f.write(contents + "\n")

    # print_invoice_to_output_file writes each field of the invoice object to results.txt
    # param: invoice: Invoice object, the invoice whose fields are to be output
    # returns: N/A
    def print_invoice_to_output_file(self, invoice):

        # Check to make sure the filepath exists
        if not os.path.exists(os.path.dirname(self.results_filepath)):
            raise FileNotFoundError(
                f"Debug file directory {os.path.dirname(self.results_filepath)} does not exist."
            )

        # If results.txt already exists, append to it, otherwise write from beginning
        if os.path.isfile(os.path.dirname(self.results_filepath)):
            write_or_append = "a"
        else:
            write_or_append = "w"

        # Write invoice contents to file
        # TODO: Should the FileIO class be responsible for paring this all out? Or the Invoice class provides
        # a to_string function or something that returns this formatting string
        with open(self.results_filepath, write_or_append) as f:
            f.write("***********************************\n")
            f.write(f"Processed Invoice Results:\n")
            f.write(f"Customer Name:    {invoice.customer_name}\n")
            f.write(f"Invoice Date:     {invoice.date}\n")
            f.write(f"Order Number:     {invoice.order_number}\n")
            f.write(f"PO Number:        {invoice.po_number}\n")
            f.write(f"Payment Terms:    {invoice.payment_terms}\n")
            f.write(f"Sales Rep:        {invoice.sales_rep}\n")
            f.write(f"Labor Cost:       ${round(invoice.labor_cost, 2)}\n")
            f.write(f"Material Cost:    ${round(invoice.material_cost, 2)}\n")
            f.write(f"Shipping Cost:    ${round(invoice.shipping_cost, 2)}\n")
            f.write(f"subtotal:         ${round(invoice.subtotal, 2)}\n")
            f.write(f"Sales Tax:        ${round(invoice.sales_tax, 2)}\n")
            f.write(f"Calculated Total: ${round(invoice.total, 2)}\n")
            f.write(f"Listed Total:     ${round(invoice.listed_total, 2)}\n")
            f.write("***********************************\n")

    # read_invoice_file is responsible for converting the given invoice PDF into a list of strings
    # Each string in the list represents a page of the invoice PDF
    # param: invoice_filepath, str: the file path of the invoice to read in
    # returns: list, a list of strings where each string is the text from a page of the invoice PDF
    def read_invoice_file(self, invoice_filepath):

        # Read text from input PDF
        pdf = PyPDF2.PdfReader(invoice_filepath)

        # Create empty list
        pages_contents = []

        # Extract text from each page and append to list
        for page in pdf.pages:
            text = page.extract_text()
            pages_contents.append(text)

        # Get Number of Pages
        return pages_contents

    # build_sales_reps_dict builds the salesReps dictionary that contains the invoice
    # code and matching name for each sales rep as defined in the sales reps config file
    # returns: dict, the populated dictionary with all codes as keys and names as values
    def build_sales_reps_dict(self):

        with open(self.sales_reps_filepath, "r") as f:
            dict = {}

            # Search through text file, only take non-comment entries
            for line in f:
                if line[0] != "*":
                    res = line.partition("=")
                    dict[res[0]] = res[2].replace(
                        "\n", ""
                    )  # Strip '\n' from all entries

        return dict

    # build_payment_terms_list builds the payment_terms list that contains each possible
    # payment term as defined in the payment terms config file
    # returns: list, contains each possible payment term that could be found in the invoice
    def build_payment_terms_list(self):

        with open(self.payment_terms_filepath, "r") as f:
            list = []

            # Search through text file, only take non-comment entries
            for line in f:
                if line[0] != "*":
                    list.append(line.replace("\n", ""))  # Strip '\n' from all entries

        return list
