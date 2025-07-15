import os
import PyPDF2

from source.Invoice import Invoice


# InvoiceAppFileIO class to handle all file input/output operations
class InvoiceAppFileIO:

    def __init__(
        self,
        debug_filepath: str,
        results_filepath: str,
        invoices_filepath: str,
        payment_terms_filepath: str,
        sales_reps_filepath: str,
    ):
        """
        Initializes the InvoiceAppFileIO object

        Args:
            debug_filepath (str): The filepath for the debug log file
            results_filepath (str): The filepath for the results log file
            invoices_filepath (str): The filepath where invoice PDFs are located
            payment_terms_filepath (str): The filepath for the payment terms config file
            sales_reps_filepath (str): The filepath for the sales reps config file
        """

        # Initialize file paths
        self.debug_filepath = debug_filepath
        self.results_filepath = results_filepath
        self.invoices_filepath = invoices_filepath
        self.payment_terms_filepath = payment_terms_filepath
        self.sales_reps_filepath = sales_reps_filepath

    def reset_debug_file(self):
        """
        Deletes the debug.txt file if it exists, to reset the debug log for the next execution
        Note: This function does nothing in the release configuration
        """

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

    def reset_results_file(self):
        """
        Deletes the results.txt file if it exists, to reset the results log for the next execution
        """

        # Check to make sure the filepath exists
        if not os.path.exists(os.path.dirname(self.debug_filepath)):
            raise FileNotFoundError(
                f"Results file path {os.path.dirname(self.results_filepath)} does not exist."
            )

        # If the file already exists, delete it
        if os.path.isfile(self.results_filepath):
            os.remove(self.results_filepath)

    def print_to_debug_file(self, contents: str):
        """
        Writes the string contents to the debug.txt file
        Note: This function does nothing in the release configuration

        Args:
            contents (str): The contents to be written to the debug file
        """

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

    def print_invoice_to_output_file(
        self, invoice: Invoice, append_output: bool = False
    ):
        """
        Writes each field of the invoice object to results.txt

        Args:
            invoice (Invoice): The invoice whose fields are to be output
            append_output (bool): Whether to append the output to the results file or overwrite it
                                    Defaults to False, meaning the results file will be overwritten
        """

        # Check to make sure the filepath exists
        if not os.path.exists(os.path.dirname(self.results_filepath)):
            raise FileNotFoundError(
                f"Debug file directory {os.path.dirname(self.results_filepath)} does not exist."
            )

        # If appending output, use "a" for the file open call, otherwise use "w"
        if append_output:
            write_or_append = "a"
        else:
            write_or_append = "w"

        # Write invoice contents to file
        with open(self.results_filepath, write_or_append) as f:
            f.write(invoice.to_formatted_string())

    def read_invoice_file(self, invoice_filepath: str) -> list:
        """
        Converts the given invoice PDF into a list of strings
        Each string in the list represents a page of the invoice PDF

        Args:
            invoice_filepath (str): The file path of the invoice to read in

        Returns:
            list: A list of strings where each string is the text from a page of the invoice
        """

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

    def build_sales_reps_dict(self) -> dict:
        """
        Builds the salesReps dictionary that contains the invoice
        code and matching name for each sales rep as defined in the sales reps config file

        Returns:
            dict: The populated dictionary with all codes as keys and names as values
        """

        # Open sales rep config file for reading
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

    def build_payment_terms_list(self) -> list:
        """
        Builds the payment_terms list that contains each possible
        payment term as defined in the payment terms config file

        Returns:
            list: A list of strings, each string is a payment term that could be found in
        """

        # Open payment terms config file for reading
        with open(self.payment_terms_filepath, "r") as f:
            list = []

            # Search through text file, only take non-comment entries
            for line in f:
                if line[0] != "*":
                    list.append(
                        line.replace("\n", "")
                    )  # Strip '\n' from all entries

        return list
