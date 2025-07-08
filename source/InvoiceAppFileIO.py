import os


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
    def reset_debug_file(self):

        # Check to make sure the filepath exists
        if not os.path.exists(self.debug_filepath - "/debug.txt"):
            raise FileNotFoundError(
                f"Debug file path {(self.debug_filepath - "/debug.txt")} does not exist."
            )

        # If the file already exists, delete it
        if os.path.isfile(self.debug_filepath):
            os.remove(self.debug_filepath)

    # reset_results_file deletes results.txt that was created from the previous program execution
    def reset_results_file(self):

        # Check to make sure the filepath exists
        if not os.path.exists(self.results_filepath - "/results.txt"):
            raise FileNotFoundError(
                f"Results file path {(self.results_filepath - "/results.txt")} does not exist."
            )

        # If the file already exists, delete it
        if os.path.isfile(self.results_filepath):
            os.remove(self.results_filepath)

    # print_to_debug_file writes the str contents to debug.txt
    # param: contents: str, the contents to be written to file
    # returns: N/A
    def print_to_debug_file(self, contents):

        # If debug.txt already exists, append to it, otherwise write from beginning
        if os.path.isfile("./debug.txt"):
            write_or_append = "a"
        else:
            write_or_append = "w"

        # Write contents to file
        with open("debug.txt", write_or_append) as f:
            f.write(contents + "\n")

    # print_to_output_file writes each field of the invoice object to results.txt
    # param: invoice: Invoice object, the invoice whose fields are to be output
    # returns: N/A
    def print_to_output_file(self, invoice):

        # If results.txt already exists, append to it, otherwise write from beginning
        if os.path.isfile("./results.txt"):
            write_or_append = "a"
        else:
            write_or_append = "w"

        # Write invoice contents to file
        with open("results.txt", write_or_append) as f:
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
