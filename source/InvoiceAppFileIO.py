import os
import PyPDF2
from typing import List

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
        cost_criteria_filepath: str,
    ):
        """
        Initializes the InvoiceAppFileIO object

        Args:
            debug_filepath (str): The filepath for the debug log
            results_filepath (str): The filepath for the results log
            invoices_filepath (str): The filepath where invoice PDFs are located
            payment_terms_filepath (str): The filepath for the payment terms config file
            sales_reps_filepath (str): The filepath for the sales reps config file
            cost_criteria_filepath (str): The filepath for the cost criteria config file
        """

        # Initialize file paths
        self.debug_filepath = debug_filepath
        self.results_filepath = results_filepath
        self.invoices_filepath = invoices_filepath
        self.payment_terms_filepath = payment_terms_filepath
        self.sales_reps_filepath = sales_reps_filepath
        self.cost_criteria_filepath = cost_criteria_filepath

        # Initialize cost criteria/exclusion lists
        self.labor_criteria = []
        self.labor_exclusions = []
        self.shipping_criteria = []

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
        with open(file=self.debug_filepath, mode=write_or_append) as f:
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
        with open(file=self.results_filepath, mode=write_or_append) as f:
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
        pdf = PyPDF2.PdfReader(stream=invoice_filepath)

        # Create empty list
        pages = []

        # Extract text from each page and append to list
        for page in pdf.pages:
            text = page.extract_text()
            pages.append(text)

        # Get Number of Pages
        return pages

    def parse_sales_reps_config(self) -> dict:
        """
        Builds the Sales Reps dictionary that contains the invoice code and
        matching name for each sales rep as defined in the sales reps config file

        Returns:
            dict: The populated dictionary with all codes as keys and names as values
        """

        # Open sales rep config file for reading
        with open(file=self.sales_reps_filepath, mode="r") as f:
            dict = {}

            # Search through text file, only take non-comment entries
            for line in f:

                # Strip whitespace from the line
                line = line.strip()

                # Skip empty lines or comment lines
                if not line or line[0] == "*":
                    continue

                res = line.partition("=")
                dict[res[0]] = res[2]

        return dict

    def parse_payment_terms_config(self) -> list:
        """
        Builds the payment_terms list that contains each possible
        payment term as defined in the payment terms config file

        Returns:
            list: A list of strings, each string is a payment term that could be found in an invoice
        """

        # Open payment terms config file for reading
        with open(file=self.payment_terms_filepath, mode="r") as f:
            list = []

            # Search through text file, only take non-comment entries
            for line in f:

                # Strip whitespace from the line
                line = line.strip()

                # Ignore line if empty or comment line
                if not line or line[0] == "*":
                    continue

                # Append the payment term to the list
                list.append(line)

        return list

    def add_cost_criteria_field(self, category: str, line: str):
        """
        Given the current category being read in the cost criteria config file, add the entry
        to the list of criteria/exclusions

        Args:
            category (str): The category of criteria being parsed
            line (str): The current line containing the criteria/exclusion
        """

        # If this is a Labor Criteria, add it to the appropriate list
        if category == "LABOR CRITERIA":
            self.labor_criteria.append(line)

        # If this is a Labor Exclusion, add it to the appropriate list
        elif category == "LABOR EXCLUSIONS":
            self.labor_exclusions.append(line)

        # If this is a Labor Exclusion, add it to the appropriate list
        elif category == "SHIPPING CRITERIA":
            self.shipping_criteria.append(line)

        # If the category cannot be read, print it to the debug file
        else:
            self.print_to_debug_file(
                f"Unknown category read out of Cost Criteria configuration file: {category}"
            )

    def parse_cost_criteria_file(self):
        """
        Reads all cost criteria/exclusions from the provided config file and stores them
        in member variables

        Args:
            category (str): The category of criteria being parsed
            line (str): The current line containing the criteria/exclusion
        """

        # Open payment terms config file for reading
        with open(file=self.cost_criteria_filepath, mode="r") as f:

            # Default to empty strings
            line = ""
            category = ""

            # Search through text file, only take non-comment entries
            for line in f:

                # Strip trailing whitespace from line, and skip comment lines
                line = line.strip()
                if not line or line[0] == "*":
                    continue

                if line.endswith(":"):
                    category = line.rstrip(":").upper()

                else:
                    self.add_cost_criteria_field(category=category, line=line)
