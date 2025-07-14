from .search_utilities import *


# InvoiceProcessor class to handle all logic for text processing on invoices
class InvoiceProcessor:

    # __init__ Constructor
    # param: file_io_controller: InvoiceAppFileIO, the file IO controller to be used
    # param: labor_criteria: str list, criteria to determine if a payment line is a labor cost
    # param: labor_exclusions: str list, criteria to exclude a payment line from being a labor cost
    # param: shipping_criteria: str list, criteria to determine if a payment line is a shipping cost
    # returns: Created InvoiceProcessor object
    def __init__(
        self, file_io_controller, labor_criteria, labor_exclusions, shipping_criteria
    ):
        self.file_io_controller = file_io_controller
        self.labor_criteria = labor_criteria
        self.labor_exclusions = labor_exclusions
        self.shipping_criteria = shipping_criteria
        return

    # populate_invoice initializes the appropriate fields of a given Invoice object
    # param: invoice: Invoice, the invoice object to be populated
    # param: sales_reps: dict, all possible sales rep codes and names
    # param: payment_terms: list, all possible payment terms
    def populate_invoice(self, invoice, sales_reps, payment_terms):

        # Get the first page of the invoice
        first_page = invoice.page_contents[0]

        invoice.order_number = search_text_by_re(first_page, "S(\d{5})")
        invoice.date = search_text_by_re(first_page, "\d{2}/\d{2}/\d{4}")
        invoice.customer_name = search_text_by_re(first_page, "Customer: .+").replace(
            "Customer: ", ""
        )
        invoice.po_number = (
            search_text_by_re(first_page, "PO Number: .+S")[:-1]
        ).replace("PO Number: ", "")
        invoice.payment_terms = find_payment_terms(first_page, payment_terms)
        invoice.sales_rep = find_sales_rep(first_page, sales_reps)

    # process_payment_line takes a given line from the payment table and processes it. This includes
    # reading the entire row, determining if the payment line refers to a labor, shipping, or
    # material cost, and find the cost. It then adds that cost to the invoice total
    # param: text: str, the current page of the invoice
    # param: line: str, the line at which the payment line starts
    # param: invoice: Invoice, the invoice struct to be modified
    # param: curr_line_num: int, the current payment line number being processed
    # returns: Invoice, the invoice that was modified
    def process_payment_line(self, text, line, invoice, curr_line_num):

        # If this line contains a subtotal, do nothing
        if "subtotal" in line:
            return

        # Only take the current payment line, remove everything before line,
        # and everything right after the next payment line
        text = text[(text.find(line)) :]
        text = text[: text.find(f"\n{curr_line_num+1} ")]

        # If the cost is listed as a quantity or hourly rate, find the cost
        ea_cost = self.find_ea_cost(text)
        hr_cost = self.find_hr_cost(text)

        # Figure out which cost to use, if neither was found, return
        if ea_cost is not None:
            line_cost = ea_cost
        elif hr_cost is not None:
            line_cost = hr_cost
        else:
            return

        # Determine if the payment line is a labor, shipping, or material cost
        is_labor_cost = self.search_for_labor(line)
        is_shipping_cost = self.search_for_shipping(line)

        # Case: Payment line contains a labor cost
        if is_labor_cost:
            self.file_io_controller.print_to_debug_file(
                f"Adding LABOR COST of {line_cost} from line {curr_line_num}"
            )
            invoice.labor_cost += line_cost
            invoice.subtotal += line_cost

        # Case: Payment line contains a shipping cost
        elif is_shipping_cost:
            self.file_io_controller.print_to_debug_file(
                f"Adding SHIPPING COST of {line_cost} from line {curr_line_num}"
            )
            invoice.shipping_cost += line_cost
            invoice.subtotal += line_cost

        # Case: Payment line contains a material cost
        else:
            self.file_io_controller.print_to_debug_file(
                f"Adding MATERIAL COST of {line_cost} from line {curr_line_num}"
            )
            invoice.material_cost += line_cost
            invoice.subtotal += line_cost

    # find_ea_cost searches the payment_lines for any listing of cost listed in quantity
    # param: payment_lines: str, the lines of text that make up the payment line
    # returns: double, the cost if found, None otherwise
    def find_ea_cost(self, payment_lines):

        # Search the payment lines for any line that contains a cost listed in quantity
        for line in payment_lines.splitlines():
            cost = search_payment_line(line, "[0-9]+ea(.*)")

            # If a valid cost is found, return it, no reason to continue searching
            if cost is not None:
                return cost

        # If no cost was found, return None
        return None

    # find_ea_cost searches the payment_lines for any listing of cost listed in quantity
    # param: payment_lines: str, the lines of text that make up the payment line
    # returns: double, the cost if found, None otherwise
    def find_hr_cost(self, payment_lines):

        # Search the payment lines for any line that contains a cost listed in hourly rate
        for line in payment_lines.splitlines():
            cost = search_payment_line(line, "[0-9]+hr(.*)")

            # If a valid cost is found, return it, no reason to continue searching
            if cost is not None:
                return cost

        # If no cost was found, return None
        return None

    # process_end_of_invoice takes the ending of the invoice starting at "Total:subtotal" and searches for
    # the sales tax and the listed total on the invoice
    # param: text: str, the invoice page to be processed
    # param: startingLine: str, the line at which the end of the invoice starts
    # parms: invoice: Invoice, the invoice object to be modified
    # returns: Invoice, the invoice that was modified
    # returns: diff, the difference between the subtotal and the listed total
    def process_end_of_invoice(self, text, startingLine, invoice):

        # Only need to process from the start of the subtotal to the end
        text = text[(text.find(startingLine)) :]

        # Find sales tax and listed total and place into invoice
        invoice.sales_tax = float(
            text.splitlines()[2].replace("$", "").replace(",", "")
        )
        invoice.listed_total = float(
            text.splitlines()[3].replace("$", "").replace(",", "")
        )

        # Calculate the difference between the subtotal and the listed total
        diff = invoice.listed_total - invoice.subtotal

        return invoice, diff

    # search_for_labor takes a given payment line and searches it for the criteria
    # and exclusions that were defined during construction
    # param: line, str, one line of text from the purchase table
    # returns: True if a labor cost, False otherwise
    def search_for_labor(self, line):

        # Check if the line contains any of the labor criteria
        for criteria in self.labor_criteria:
            if criteria in line:

                # If the line contains any of the labor exclusions, return False
                for exclusion in self.labor_exclusions:
                    if exclusion in line:
                        return False

                # If the line does not contain any of the exclusions, return True
                return True

    # search_for_shipping takes a given payment line and searches it for the critieria
    # defined during construction
    # param: line, str, one line of text from the purchase table
    # returns: True if a shipping cost, False otherwise
    def search_for_shipping(self, line):

        # Check if the line contains any of the shipping criteria
        for criteria in self.shipping_criteria:
            if criteria in line:
                return True

        return False

    # process_invoice is the main function that processes the invoice pdf
    # param: invoice: Invoice, the empty invoice object to be populated
    # returns: a constructed Invoice object with all fields populated, and the difference
    # between the calculated total and the listed total, to show any discrepancies
    def process_invoice(self, invoice):

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
                    self.process_payment_line(page, line, invoice, next_line_num)
                    next_line_num += 1  # Update next_line_num

                # "Total:Subtotal" is the beginning of the end of the invoice
                if "Total:Subtotal" in line:
                    invoice, diff = self.process_end_of_invoice(page, line, invoice)

        # Calculate total from subtotal and sales tax
        invoice.calculate_total()

        return invoice, diff
