import re

from .InvoiceAppFileIO import *  # TODO: Remove this, the processor shouldn't need to know about the file IO, let the controller handle it

from .Invoice import Invoice


# InvoiceProcessor class to handle all logic for text processing on invoices
class InvoiceProcessor:

    # __init__ Constructor
    # returns: Created InvoiceProcessor object
    def __init__(self):
        return

    # search_invoice takes a given regex and searches the invoice for a match
    # param: text: str, first page of the invoice
    # param: regex: str, regex to be matched
    # returns: Either returns the str match of the regex if successful, or None
    def search_invoice(self, text, regex):
        res = re.search(regex, text)

        if res:
            return res.group()
        else:
            return None

    # search_payment_line takes a given regex and searches one line of payment text
    # from the purchase table of the invoice
    # param: line: str, one line of text from the purchase table
    # param: regex: str, regex to be matched
    # returns: N/A
    def search_payment_line(self, line, regex):
        res = re.search(regex, line)

        if res:
            return float((res.group().split()[2]).replace(",", ""))
        else:
            return -1

    # populate_invoice initializes the appropriate fields of a given Invoice object
    # param: text: str taken from the first page of the invoice
    # param: sales_reps: dict, all possible sales rep codes and names
    # param: payment_terms: list, all possible payment terms
    def populate_invoice(self, text, sales_reps, payment_terms):
        self.order_number = self.search_invoice(text, "S(\d{5})")
        self.date = self.search_invoice(text, "\d{2}/\d{2}/\d{4}")
        self.customer_name = self.search_invoice(text, "Customer: .+").replace(
            "Customer: ", ""
        )
        self.po_number = (self.search_invoice(text, "PO Number: .+S")[:-1]).replace(
            "PO Number: ", ""
        )
        self.payment_terms = self.find_payment_terms(text, payment_terms)
        self.sales_rep = self.find_sales_rep(text, sales_reps)

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
            return invoice

        # Only take the current payment line, remove everything before line,
        # and everything right after the next payment line
        text = text[(text.find(line)) :]
        text = text[: text.find(f"\n{curr_line_num+1} ")]

        # Determine if the payment line is a labor, shipping, or material cost
        is_labor_cost = self.search_for_labor(line)
        is_shipping_cost = self.search_for_shipping(line)

        # If the cost is listed as a quantity or hourly rate, find the cost
        ea_cost = self.find_ea_cost(text)
        hr_cost = self.find_hr_cost(text)

        # Case: Payment line is a labor cost
        if is_labor_cost:
            if ea_cost > -1:
                invoice.labor_cost += ea_cost
                invoice.subtotal += ea_cost
                # if __debug__:
                #     print_to_debug_file(
                #         f"Line {curr_line_num}: Adding LABOR COST of:    ${ea_cost}"
                #     )
            elif hr_cost > -1:
                invoice.labor_cost += hr_cost
                invoice.subtotal += hr_cost
                # if __debug__:
                #     print_to_debug_file(
                #         f"Line {curr_line_num}: Adding LABOR COST of:    ${hr_cost}"
                #     )

        # Case: Payment line is a shipping cost
        elif is_shipping_cost:
            if ea_cost > -1:
                invoice.shipping_cost += ea_cost
                invoice.subtotal += ea_cost
                # if __debug__:
                #     print_to_debug_file(
                #         f"Line {curr_line_num}: Adding SHIPPING COST of:    ${ea_cost}"
                #     )
            elif hr_cost > -1:
                invoice.shipping_cost += hr_cost
                invoice.subtotal += hr_cost
                # if __debug__:
                #     print_to_debug_file(
                #         f"Line {curr_line_num}: Adding SHIPPING COST of:    ${hr_cost}"
                #     )

        # Case: Payment line is a material cost
        else:
            if ea_cost > -1:
                invoice.material_cost += ea_cost
                invoice.subtotal += ea_cost
                # if __debug__:
                #     print_to_debug_file(
                #         f"Line {curr_line_num}: Adding MATERIAL COST of:    ${ea_cost}"
                #     )
            elif hr_cost > -1:
                invoice.material_cost += hr_cost
                invoice.subtotal += hr_cost
                # if __debug__:
                #     print_to_debug_file(
                #         f"Line {curr_line_num}: Adding MATERIAL COST of:    ${hr_cost}"
                #     )

        return invoice

    # find_ea_cost searches the payment_lines for any listing of cost listed in quantity
    # param: payment_lines: str, the lines of text that make up the payment line
    # returns: double, the cost if found, -1 if otherwise
    def find_ea_cost(self, payment_lines):

        for line in payment_lines.splitlines():
            cost = self.search_payment_line(line, "[0-9]+ea(.*)")
            if cost > -1:
                return cost

        return -1

    # find_ea_cost searches the payment_lines for any listing of cost listed in quantity
    # param: payment_lines: str, the lines of text that make up the payment line
    # returns: double, the cost if found, -1 if otherwise
    def find_hr_cost(self, payment_lines):

        for line in payment_lines.splitlines():
            cost = self.search_payment_line(line, "[0-9]+hr(.*)")
            if cost > -1:
                return cost

        return -1

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

    # search_for_labor takes a given payment line and searches it for markers
    # that would indicate that this line contains a labor cost
    # param: line, str, one line of text from the purchase table
    # returns: True if a labor cost, False otherwise
    def search_for_labor(self, line):

        # Only return true is MF/ or MD/ was found in the line. Does not include
        # MF/RHR or MF/LHR or MD/RHR or MD/LHR
        if (("MF/" in line) or ("MD/" in line)) and (
            ("MF/RHR" not in line)
            and ("MF/LHR" not in line)
            and ("MD/RHR" not in line)
            and ("MD/LHR" not in line)
        ):
            return True
        else:
            return False

    def search_for_shipping(self, line):

        if ("DELIVERY" in line) or ("UPS GROUND" in line) or ("FREIGHT OUT" in line):
            return True

        return False

    # find_payment_terms takes the invoice and searches for an occurance of any
    # of the possible payment terms
    # param: text: str, the invoice to be searched
    # param: payment_terms: dict, contains all possible payment terms
    # returns: str, payment term if match found, "Could Not Find" otherwise
    def find_payment_terms(self, text, payment_terms):

        # Search for each possible payment term
        for term in payment_terms:
            res = re.search(term, text)

            # If found, return the term
            if res:
                return term

        return "Could Not Find"

    # find_sales_rep takes the invoice and searched for the sales rep listed
    # param: text: str, the invoice to be searched
    # param: sales_reps: dict, contains all possible sales rep codes and names
    # returns: str, the name of the sales rep if found, "Could Not Find" otherwise
    def find_sales_rep(self, text, sales_reps):

        # Search for each possible sales rep
        for key, val in sales_reps.items():
            res = re.search(key, text)

            # If found, return sales rep name
            if res:
                return val

        return "Could Not Find"

    # get_filename_from_filepath takes a full filepath to an invoice PDF file and
    # isolates the name of the file
    # param: str: filepath, the full path to the invoice pdf
    # returns: the filename "xxxx.pdf" if found, -1 if not found
    def get_filename_from_filepath(self, filepath):
        res = re.search("SO-(.+).pdf", filepath)

        if res:
            return res.group()
        else:
            return -1

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
                    invoice = self.process_payment_line(
                        page, line, invoice, next_line_num
                    )
                    next_line_num += 1  # Update nextLineNum

                # "Total:Subtotal" is the beginning of the end of the invoice
                if "Total:Subtotal" in line:
                    invoice, diff = self.process_end_of_invoice(page, line, invoice)

        # Calculate total from subtotal and sales tax
        invoice.calculate_total()

        return invoice, diff
