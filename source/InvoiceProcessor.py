from source.processor_utilities import *
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.Invoice import Invoice
from source.globals import *


# InvoiceProcessor class to handle all logic for text processing on invoices
class InvoiceProcessor:

    def __init__(
        self,
        file_io_controller: InvoiceAppFileIO,
        labor_criteria: list,
        labor_exclusions: list,
        shipping_criteria: list,
    ):
        """
        Initializes the InvoiceProcessor object

        Args:
            file_io_controller (InvoiceAppFileIO): The file IO controller to be used
            labor_criteria (list): Criteria to determine if a payment line is a labor cost
            labor_exclusions (list): Criteria to exclude a payment line from being a labor cost
            shipping_criteria (list): Criteria to determine if a payment line is a shipping cost
        """

        self.file_io_controller = file_io_controller
        self.labor_criteria = labor_criteria
        self.labor_exclusions = labor_exclusions
        self.shipping_criteria = shipping_criteria
        return

    def populate_invoice(
        self, invoice: Invoice, sales_reps: dict, payment_terms: list
    ):
        """
        Initializes all fields of an invoice object that appear on the first page of the invoice PDF

        Args:
            invoice (Invoice): The invoice object to be populated
            sales_reps (dict): All possible sales rep codes and names
            payment_terms (list): All possible payment terms
        """

        if invoice is None:
            raise ValueError("Cannot parse a None invoice object")

        # Get the first page of the invoice
        first_page = invoice.page_contents[0]

        # Parse the first page to get the invoice attributes
        invoice.order_number = search_text_by_re(
            text=first_page, regex=r"S(\d{5})"
        )
        invoice.date = search_text_by_re(
            text=first_page, regex=r"\d{2}/\d{2}/\d{4}"
        )

        # Customer name will also match "Customer: " to the string, so trim it off
        invoice.customer_name = search_text_by_re(
            text=first_page, regex=r"Customer: .+"
        ).replace("Customer: ", "")

        # PO Number will also match "PO Number: " to the string, so trim it off
        # It will also match other strings, so need to take the last element only
        invoice.po_number = (
            search_text_by_re(text=first_page, regex=r"PO Number: .+S")[:-1]
        ).replace("PO Number: ", "")
        invoice.payment_terms = find_payment_terms(
            text=first_page, payment_terms=payment_terms
        )
        invoice.sales_rep = find_sales_rep(
            text=first_page, sales_reps=sales_reps
        )

    def process_payment_line(
        self, text: str, line: str, invoice: Invoice, curr_line_num: int
    ):
        """
        Takes a given line from the payment table and processes it.
        This includes reading the entire row, determining if the payment line refers to a labor,
        shipping, or material cost, and finding the cost. It then adds that cost to the invoice total

        Args:
            text (str): The current page of the invoice
            line (str): The line at which the payment line starts
            invoice (Invoice): The invoice object to be modified
            curr_line_num (int): The current payment line number being processed
        """

        # If this line contains a subtotal, do nothing
        if "subtotal" in line:
            return

        # Only take the current payment line, remove everything before line,
        # and everything right after the next payment line
        text = text[(text.find(line)) :]
        text = text[: text.find(f"\n{curr_line_num+1} ")]

        # If the cost is listed as a quantity or hourly rate, find the cost
        ea_cost = self.find_ea_cost(payment_lines=text)
        hr_cost = self.find_hr_cost(payment_lines=text)

        # Figure out which cost to use, if neither was found, return
        if ea_cost > DECIMAL_ZERO:
            line_cost = ea_cost
        elif hr_cost > DECIMAL_ZERO:
            line_cost = hr_cost
        else:
            return

        # Determine if the payment line is a labor, shipping, or material cost
        is_labor_cost = self.search_for_labor_criteria(line=line)
        is_shipping_cost = self.search_for_shipping(line=line)

        # Case: Payment line contains a labor cost
        if is_labor_cost:
            self.file_io_controller.print_to_debug_file(
                contents=f"Adding LABOR COST of {line_cost} from line {curr_line_num}"
            )
            invoice.labor_cost += format_currency(value=line_cost)
            invoice.subtotal += format_currency(value=line_cost)

        # Case: Payment line contains a shipping cost
        elif is_shipping_cost:
            self.file_io_controller.print_to_debug_file(
                contents=f"Adding SHIPPING COST of {line_cost} from line {curr_line_num}"
            )
            invoice.shipping_cost += format_currency(value=line_cost)
            invoice.subtotal += format_currency(value=line_cost)

        # Case: Payment line contains a material cost
        else:
            self.file_io_controller.print_to_debug_file(
                contents=f"Adding MATERIAL COST of {line_cost} from line {curr_line_num}"
            )
            invoice.material_cost += format_currency(value=line_cost)
            invoice.subtotal += format_currency(value=line_cost)

    def find_ea_cost(self, payment_lines: str) -> Decimal:
        """
        Searches the payment_lines for any listing of cost listed in quantity

        Args:
            payment_lines (str): The lines of text that make up the payment line

        Returns:
            Decimal: The cost if found, 0.0 otherwise
        """

        # Search the payment lines for any line that contains a cost listed in quantity
        for line in payment_lines.splitlines():
            cost = search_payment_line(line=line, regex=r"[0-9]+\s*ea(.*)")

            # If a valid cost is found, return it, no reason to continue searching
            if cost > DECIMAL_ZERO:
                return format_currency(value=cost)

        # If no cost was found, return 0.0
        return DECIMAL_ZERO

    def find_hr_cost(self, payment_lines: str) -> Decimal:
        """
        Searches the payment_lines for any listing of cost listed in hourly rate

        Args:
            payment_lines (str): The lines of text that make up the payment line

        Returns:
            Decimal: The cost if found, 0.0 otherwise
        """

        # Search the payment lines for any line that contains a cost listed in hourly rate
        for line in payment_lines.splitlines():
            cost = search_payment_line(line=line, regex=r"[0-9]+\s*hr(.*)")

            # If a valid cost is found, return it, no reason to continue searching
            if cost > DECIMAL_ZERO:
                return format_currency(value=cost)

        # If no cost was found, return None
        return DECIMAL_ZERO

    def process_end_of_invoice(
        self, text: str, starting_line: str, invoice: Invoice
    ):
        """
        Takes the ending of the invoice starting at "Total:subtotal" and searches for
        the sales tax and the listed total on the invoice

        Args:
            text (str): The invoice page to be processed
            starting_line (str): The line at which the end of the invoice starts
            invoice (Invoice): The invoice object to be modified
        """

        # Only need to process from the start of the subtotal to the end
        text = text[(text.find(starting_line)) :]

        # Find sales tax and listed total and place into invoice
        invoice.sales_tax = Decimal(
            text.splitlines()[2].replace("$", "").replace(",", "")
        )
        invoice.listed_total = Decimal(
            text.splitlines()[3].replace("$", "").replace(",", "")
        )

        # Calculate the total of all processed listed costs
        invoice.total = format_currency(
            value=invoice.subtotal
        ) + format_currency(value=invoice.sales_tax)

    def search_for_labor_criteria(self, line: str) -> bool:
        """
        Takes a given payment line and searches it for the criteria
        and exclusions that were defined during construction

        Args:
            line (str): One line of text from the purchase table

        Returns:
            bool: True if a labor cost, False otherwise
        """

        # Check if the line contains any of the labor criteria
        for criteria in self.labor_criteria:
            if criteria in line:

                # If the line contains any of the labor exclusions, return False
                for exclusion in self.labor_exclusions:
                    if exclusion in line:
                        return False

                # If the line does not contain any of the exclusions, return True
                return True

        # If no labor criteria was found, return False
        return False

    def search_for_shipping(self, line: str) -> bool:
        """
        Takes a given payment line and searches it for the criteria
        that was defined during construction

        Args:
            line (str): One line of text from the purchase table

        Returns:
            bool: True if a shipping cost, False otherwise
        """

        # Check if the line contains any of the shipping criteria
        for criteria in self.shipping_criteria:
            if criteria in line:
                return True

        return False

    def process_invoice(self, invoice: Invoice):
        """
        Main function that processes the invoice PDF

        Args:
            invoice (Invoice): The empty invoice object to be populated
        """

        # Keep track of next expected payment line number
        next_line_num = 1

        # Loop through each page to read purchase table
        for page in invoice.page_contents:

            # At this point, can disregard everything before the purchase table
            # Trim off everything before purchase table (before the line Ordered Total Price)
            if len(page[(page.find("Ordered Total Price")) :]) > 1:
                page = page[(page.find("Ordered Total Price")) :]

            # Loop through each line in the table. Some table entries may have multiple lines that need
            # to be processed
            for line in page.splitlines():

                # Check if at beginning of the line in the table. If so, process this payment item
                if line.startswith(f"{next_line_num} "):
                    self.process_payment_line(
                        text=page,
                        line=line,
                        invoice=invoice,
                        curr_line_num=next_line_num,
                    )
                    next_line_num += 1  # Update next_line_num

                # "Total:Subtotal" is the beginning of the end of the invoice
                if "Total:Subtotal" in line:
                    self.process_end_of_invoice(
                        text=page, starting_line=line, invoice=invoice
                    )
