from decimal import Decimal

from source.constants import DECIMAL_ZERO
from source.Invoice import Invoice
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.processor_utilities import (
    find_currency_values,
    find_payment_terms,
    find_sales_rep,
    format_currency,
    search_payment_line,
    search_text_by_re,
)

# The last label in the invoice's footer. pypdf emits the footer's label column
# before its value column, so this label is followed by every footer amount in
# order -- subtotal, sales tax, listed total -- rather than by its own value:
#
#     Total:Subtotal:
#     Sales Tax:$1,234.56   <- the last label, then the SUBTOTAL
#     $46.54                <- sales tax
#     $1,281.10             <- listed total
#
# Anchoring here and reading the amounts in order is therefore what locates them
# by label. Matching an amount on the label's own line would read the subtotal.
FOOTER_VALUE_LABEL = "Sales Tax:"

# How many amounts the footer lists: subtotal, sales tax, and the listed total
FOOTER_VALUE_COUNT = 3


# InvoiceProcessor class to handle all logic for text processing on invoices
class InvoiceProcessor:
    ###########################################################################
    ###                   InvoiceProcessor -> __init__()                    ###
    ###########################################################################
    def __init__(
        self,
        file_io_controller: InvoiceAppFileIO,
        labor_criteria: list[str],
        labor_exclusions: list[str],
        shipping_criteria: list[str],
    ) -> None:
        """
        Initializes the InvoiceProcessor object

        Args:
            file_io_controller: The file IO controller to be used
            labor_criteria: Criteria to determine if a payment line is a labor cost
            labor_exclusions: Criteria to exclude a payment line from being a labor cost
            shipping_criteria: Criteria to determine if a payment line is a shipping cost
        """

        self.file_io_controller = file_io_controller
        self.labor_criteria = labor_criteria
        self.labor_exclusions = labor_exclusions
        self.shipping_criteria = shipping_criteria

    ###########################################################################
    ###               InvoiceProcessor -> populate_invoice()                ###
    ###########################################################################
    def populate_invoice(self, invoice: Invoice, sales_reps: dict[str, str], payment_terms: list[str]) -> None:
        """
        Initializes all fields of an invoice object that appear on the first page of the invoice PDF

        Args:
            invoice: The invoice object to be populated
            sales_reps: All possible sales rep codes and names
            payment_terms: All possible payment terms
        """

        if invoice is None:
            # TRY003 is suppressed rather than satisfied: a dedicated exception
            # class for one internal guard against a programming error is more
            # indirection than a single call site earns.
            raise ValueError("Cannot parse a None invoice object")  # noqa: TRY003

        # Get the first page of the invoice
        first_page = invoice.page_contents[0]

        # Parse the first page to get the invoice attributes
        invoice.order_number = search_text_by_re(text=first_page, regex=r"S(\d{5})")
        invoice.date = search_text_by_re(text=first_page, regex=r"\d{2}/\d{2}/\d{4}")

        # Customer name will also match "Customer: " to the string, so trim it off
        invoice.customer_name = search_text_by_re(text=first_page, regex=r"Customer: .+").replace("Customer: ", "")

        # PO Number will also match "PO Number: " to the string, so trim it off
        # It will also match other strings, so need to take the last element only
        invoice.po_number = (search_text_by_re(text=first_page, regex=r"PO Number: .+S")[:-1]).replace(
            "PO Number: ", ""
        )
        invoice.payment_terms = find_payment_terms(text=first_page, payment_terms=payment_terms)
        invoice.sales_rep = find_sales_rep(text=first_page, sales_reps=sales_reps)

    ###########################################################################
    ###             InvoiceProcessor -> process_payment_line()              ###
    ###########################################################################
    def process_payment_line(self, text: str, line: str, invoice: Invoice, curr_line_num: int) -> None:
        """
        Takes a given line from the payment table and processes it.
        This includes reading the entire row, determining if the payment line refers to a labor,
        shipping, or material cost, and finding the cost. It then adds that cost to the invoice total

        Args:
            text: The current page of the invoice
            line: The line at which the payment line starts
            invoice: The invoice object to be modified
            curr_line_num: The current payment line number being processed
        """

        # If this line contains a subtotal, do nothing
        if "subtotal" in line:
            return

        # Only take the current payment line, remove everything before line,
        # and everything right after the next payment line
        text = text[(text.find(line)) :]
        text = text[: text.find(f"\n{curr_line_num + 1} ")]

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
        is_shipping_cost = self.search_for_shipping_criteria(line=line)

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

    ###########################################################################
    ###                 InvoiceProcessor -> find_ea_cost()                  ###
    ###########################################################################
    def find_ea_cost(self, payment_lines: str) -> Decimal:
        """
        Searches the payment_lines for any listing of cost listed in quantity

        Args:
            payment_lines: The lines of text that make up the payment line

        Returns:
            The cost if found, 0.0 otherwise
        """

        # Search the payment lines for any line that contains a cost listed in quantity
        for line in payment_lines.splitlines():
            cost = search_payment_line(line=line, regex=r"[0-9]+\s*ea(.*)")

            # If a valid cost is found, return it, no reason to continue searching
            if cost > DECIMAL_ZERO:
                return format_currency(value=cost)

        # If no cost was found, return 0.0
        return DECIMAL_ZERO

    ###########################################################################
    ###                 InvoiceProcessor -> find_hr_cost()                  ###
    ###########################################################################
    def find_hr_cost(self, payment_lines: str) -> Decimal:
        """
        Searches the payment_lines for any listing of cost listed in hourly rate

        Args:
            payment_lines: The lines of text that make up the payment line

        Returns:
            The cost if found, 0.0 otherwise
        """

        # Search the payment lines for any line that contains a cost listed in hourly rate
        for line in payment_lines.splitlines():
            cost = search_payment_line(line=line, regex=r"[0-9]+\s*hr(.*)")

            # If a valid cost is found, return it, no reason to continue searching
            if cost > DECIMAL_ZERO:
                return format_currency(value=cost)

        # If no cost was found, return None
        return DECIMAL_ZERO

    ###########################################################################
    ###            InvoiceProcessor -> process_end_of_invoice()             ###
    ###########################################################################
    def process_end_of_invoice(self, text: str, starting_line: str, invoice: Invoice) -> None:
        """
        Takes the ending of the invoice starting at "Total:subtotal" and searches for
        the sales tax and the listed total on the invoice

        Args:
            text: The invoice page to be processed
            starting_line: The line at which the end of the invoice starts
            invoice: The invoice object to be modified
        """

        # Only need to process from the start of the subtotal to the end
        text = text[(text.find(starting_line)) :]

        # Anchor on the footer's last label, so the amounts are located by what
        # precedes them rather than by their line number
        label_index = text.find(FOOTER_VALUE_LABEL)
        values = find_currency_values(text=text[label_index:])[:FOOTER_VALUE_COUNT] if label_index != -1 else []

        # A footer missing its label, or listing fewer amounts than expected, means
        # the invoice cannot be read. Report it and leave the amounts at zero rather
        # than guessing at a value the user's total would then be compared against
        if len(values) < FOOTER_VALUE_COUNT:
            self.file_io_controller.report_error(
                "Invoice Parse Error",
                f"Could not read the sales tax and listed total from invoice {invoice.order_number}.",
            )
            invoice.sales_tax = DECIMAL_ZERO
            invoice.listed_total = DECIMAL_ZERO
        else:
            # The first amount is the invoice's own subtotal, which is deliberately
            # discarded: the subtotal on the invoice object is summed from the payment
            # lines, and reporting where the two disagree is the point of the app
            invoice.sales_tax = values[1]
            invoice.listed_total = values[2]

        # Calculate the total of all processed listed costs
        invoice.total = format_currency(value=invoice.subtotal) + format_currency(value=invoice.sales_tax)

    ###########################################################################
    ###           InvoiceProcessor -> search_for_labor_criteria()           ###
    ###########################################################################
    def search_for_labor_criteria(self, line: str) -> bool:
        """
        Takes a given payment line and searches it for the criteria
        and exclusions that were defined during construction

        Args:
            line: One line of text from the purchase table

        Returns:
            True if a labor cost, False otherwise
        """

        # Check if the line contains any of the labor criteria
        for criteria in self.labor_criteria:
            if criteria in line:
                # A matched line still is not labor if it names an exclusion
                return all(exclusion not in line for exclusion in self.labor_exclusions)

        # If no labor criteria was found, return False
        return False

    ###########################################################################
    ###         InvoiceProcessor -> search_for_shipping_criteria()          ###
    ###########################################################################
    def search_for_shipping_criteria(self, line: str) -> bool:
        """
        Takes a given payment line and searches it for the criteria
        that was defined during construction

        Args:
            line: One line of text from the purchase table

        Returns:
            True if a shipping cost, False otherwise
        """

        # Check if the line contains any of the shipping criteria
        return any(criteria in line for criteria in self.shipping_criteria)

    ###########################################################################
    ###                InvoiceProcessor -> process_invoice()                ###
    ###########################################################################
    def process_invoice(self, invoice: Invoice) -> None:
        """
        Main function that processes the invoice PDF

        Args:
            invoice: The empty invoice object to be populated
        """

        # Keep track of next expected payment line number
        next_line_num = 1

        # Loop through each page to read purchase table
        for page in invoice.page_contents:
            # At this point, can disregard everything before the purchase table
            # Trim off everything before purchase table (before the line Ordered Total Price)
            table_text = page
            if len(page[(page.find("Ordered Total Price")) :]) > 1:
                table_text = page[(page.find("Ordered Total Price")) :]

            # Loop through each line in the table. Some table entries may have multiple lines that need
            # to be processed
            for line in table_text.splitlines():
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
                    self.process_end_of_invoice(text=page, starting_line=line, invoice=invoice)
