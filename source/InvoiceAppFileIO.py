import PyPDF2
from pathlib import Path
from typing import Callable

from source.Invoice import Invoice
from source.constants import (
    DEBUG_LOG_PATH,
    RESULTS_LOG_PATH,
    PAYMENT_TERMS_PATH,
    SALES_REPS_PATH,
    COST_CRITERIA_PATH,
)


# InvoiceAppFileIO class to handle all file input/output operations
class InvoiceAppFileIO:

    ###########################################################################
    ###                   InvoiceAppFileIO -> __init__()                    ###
    ###########################################################################
    def __init__(self, report_error: Callable[[str, str], None] = lambda *_: None):
        """
        Initializes the InvoiceAppFileIO object

        Args:
            report_error (Callable[[str, str], None]): Callback used to surface a
                file I/O failure to the user, taking an error title and message.
                Defaults to a no-op so file I/O never depends on a reporter being
                wired in (the controller injects the GUI's error popup)
        """

        # Callback used to report file I/O failures to the user
        self.report_error = report_error

        # Initialize cost criteria/exclusion lists
        self.labor_criteria = []
        self.labor_exclusions = []
        self.shipping_criteria = []

    ###########################################################################
    ###                InvoiceAppFileIO -> reset_debug_file()               ###
    ###########################################################################
    def reset_debug_file(self):
        """
        Deletes the debug.txt file if it exists, to reset the debug log for the next execution
        Note: This function does nothing in the release configuration
        """

        # If in release configuration, do nothing
        if not __debug__:
            return

        try:
            # Ensure the log directory exists, then delete the debug file if present
            DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            if DEBUG_LOG_PATH.is_file():
                DEBUG_LOG_PATH.unlink()

        except OSError as error:
            self.report_error(
                "File Error",
                f"Could not reset the debug log at {DEBUG_LOG_PATH}: {error}",
            )

    ###########################################################################
    ###               InvoiceAppFileIO -> reset_results_file()             ###
    ###########################################################################
    def reset_results_file(self):
        """
        Deletes the results.txt file if it exists, to reset the results log for the next execution
        """

        try:
            # Ensure the log directory exists, then delete the results file if present
            RESULTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            if RESULTS_LOG_PATH.is_file():
                RESULTS_LOG_PATH.unlink()

        except OSError as error:
            self.report_error(
                "File Error",
                f"Could not reset the results log at {RESULTS_LOG_PATH}: {error}",
            )

    ###########################################################################
    ###              InvoiceAppFileIO -> print_to_debug_file()              ###
    ###########################################################################
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

        try:
            # Ensure the log directory exists, then append the contents
            DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(file=DEBUG_LOG_PATH, mode="a") as f:
                f.write(contents + "\n")

        except OSError as error:
            self.report_error(
                "File Error",
                f"Could not write to the debug log at {DEBUG_LOG_PATH}: {error}",
            )

    ###########################################################################
    ###         InvoiceAppFileIO -> print_invoice_to_output_file()          ###
    ###########################################################################
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

        # If appending output, use "a" for the file open call, otherwise use "w"
        if append_output:
            write_or_append = "a"
        else:
            write_or_append = "w"

        try:
            # Ensure the log directory exists, then write the invoice contents
            RESULTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(file=RESULTS_LOG_PATH, mode=write_or_append) as f:
                f.write(invoice.to_formatted_string())

        except OSError as error:
            self.report_error(
                "File Error",
                f"Could not write to the results log at {RESULTS_LOG_PATH}: {error}",
            )

    ###########################################################################
    ###                InvoiceAppFileIO -> read_text_file()                 ###
    ###########################################################################
    def read_text_file(self, file_path: Path) -> str:
        """
        Reads the full contents of a text file into a single string

        Args:
            file_path (Path): The file path of the text file to read in

        Returns:
            str: The full contents of the file, or an empty string if the file
                could not be read
        """

        try:
            # Open the file for reading and return its full contents
            with open(file=file_path, mode="r") as f:
                return f.read()

        except OSError as error:
            self.report_error(
                "File Error",
                f"Could not read the file at {file_path}: {error}",
            )
            return ""

    ###########################################################################
    ###                InvoiceAppFileIO -> write_text_file()                ###
    ###########################################################################
    def write_text_file(self, file_path: Path, contents: str):
        """
        Writes the given string contents to a text file, overwriting any existing
        contents

        Args:
            file_path (Path): The file path of the text file to write to
            contents (str): The contents to write to the file
        """

        try:
            # Ensure the parent directory exists, then overwrite the file contents
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file=file_path, mode="w") as f:
                f.write(contents)

        except OSError as error:
            self.report_error(
                "File Error",
                f"Could not write to the file at {file_path}: {error}",
            )

    ###########################################################################
    ###               InvoiceAppFileIO -> read_invoice_file()               ###
    ###########################################################################
    def read_invoice_file(self, invoice_filepath: Path) -> list:
        """
        Converts the given invoice PDF into a list of strings
        Each string in the list represents a page of the invoice PDF

        Args:
            invoice_filepath (Path): The file path of the invoice to read in

        Returns:
            list: A list of strings where each string is the text from a page of the
                invoice, or an empty list if the PDF could not be read
        """

        try:
            # Read text from input PDF
            pdf = PyPDF2.PdfReader(stream=invoice_filepath)

            # Extract text from each page and append to list
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                pages.append(text)

            return pages

        except (OSError, PyPDF2.errors.PdfReadError) as error:
            self.report_error(
                "File Error",
                f"Could not read the invoice PDF at {invoice_filepath}: {error}",
            )
            return []

    ###########################################################################
    ###            InvoiceAppFileIO -> parse_sales_reps_config()            ###
    ###########################################################################
    def parse_sales_reps_config(self) -> dict:
        """
        Builds the Sales Reps dictionary that contains the invoice code and
        matching name for each sales rep as defined in the sales reps config file

        Returns:
            dict: The populated dictionary with all codes as keys and names as
                values, or an empty dictionary if the config file could not be read
        """

        sales_reps = {}

        try:
            # Open sales rep config file for reading
            with open(file=SALES_REPS_PATH, mode="r") as f:

                # Search through text file, only take non-comment entries
                for line in f:

                    # Strip whitespace from the line
                    line = line.strip()

                    # Skip empty lines or comment lines
                    if not line or line[0] == "*":
                        continue

                    res = line.partition("=")

                    # Res[0] is the sales rep code, res[2] is the sales rep name translation
                    sales_reps[res[0]] = res[2]

        except OSError as error:
            self.report_error(
                "Config Error",
                f"Could not read the sales reps config at {SALES_REPS_PATH}: {error}",
            )

        return sales_reps

    ###########################################################################
    ###          InvoiceAppFileIO -> parse_payment_terms_config()           ###
    ###########################################################################
    def parse_payment_terms_config(self) -> list:
        """
        Builds the payment_terms list that contains each possible
        payment term as defined in the payment terms config file

        Returns:
            list: A list of strings, each string is a payment term that could be
                found in an invoice, or an empty list if the config could not be read
        """

        payment_terms = []

        try:
            # Open payment terms config file for reading
            with open(file=PAYMENT_TERMS_PATH, mode="r") as f:

                # Search through text file, only take non-comment entries
                for line in f:

                    # Strip whitespace from the line
                    line = line.strip()

                    # Ignore line if empty or comment line
                    if not line or line[0] == "*":
                        continue

                    # Append the payment term to the list
                    payment_terms.append(line)

        except OSError as error:
            self.report_error(
                "Config Error",
                f"Could not read the payment terms config at {PAYMENT_TERMS_PATH}: {error}",
            )

        return payment_terms

    ###########################################################################
    ###            InvoiceAppFileIO -> add_cost_criteria_field()            ###
    ###########################################################################
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

    ###########################################################################
    ###           InvoiceAppFileIO -> parse_cost_criteria_file()            ###
    ###########################################################################
    def parse_cost_criteria_file(self):
        """
        Reads all cost criteria/exclusions from the provided config file and stores them
        in member variables
        """

        # Clear the criteria lists in place so re-parsing (e.g. after the user
        # saves an edited config) replaces the previous contents rather than
        # appending to them. Clearing in place rather than reassigning keeps the
        # references held by the InvoiceProcessor pointed at the same lists.
        self.labor_criteria.clear()
        self.labor_exclusions.clear()
        self.shipping_criteria.clear()

        try:
            # Open cost criteria config file for reading
            with open(file=COST_CRITERIA_PATH, mode="r") as f:

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

        except OSError as error:
            self.report_error(
                "Config Error",
                f"Could not read the cost criteria config at {COST_CRITERIA_PATH}: {error}",
            )
