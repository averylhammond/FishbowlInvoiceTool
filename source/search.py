import re
from source.fio import *


# search_invoice takes a given regex and searches the invoice for a match
# params: text: str, first page of the invoice
# params: regex: str, regex to be matched
# returns: Either returns the str match of the regex if successful, or None
def search_invoice(text, regex):
    res = re.search(regex, text)

    if res:
        return res.group()
    else:
        return None


# search_payment_line takes a given regex and searches one line of payment text
# from the purchase table of the invoice
# params: line: str, one line of text from the purchase table
# params: regex: str, regex to be matched
# returns: N/A
def search_payment_line(line, regex):
    res = re.search(regex, line)

    if res:
        return float((res.group().split()[2]).replace(",", ""))
    else:
        return -1


# process_payment_line takes a given line from the payment table and processes it. This includes
# reading the entire row, determining if the payment line refers to a labor, shipping, or
# material cost, and find the cost. It then adds that cost to the invoice total
# params: text: str, the current page of the invoice
# params: line: str, the line at which the payment line starts
# params: invoice: Invoice, the invoice struct to be modified
# params: curr_line_num: int, the current payment line number being processed
# returns: Invoice, the invoice that was modified
def process_payment_line(text, line, invoice, curr_line_num):

    # If this line contains a subtotal, do nothing
    if "subtotal" in line:
        return invoice

    # Only take the current payment line, remove everything before line,
    # and everything right after the next payment line
    text = text[(text.find(line)) :]
    text = text[: text.find(f"\n{curr_line_num+1} ")]

    # Determine if the payment line is a labor, shipping, or material cost
    is_labor_cost = search_for_labor(line)
    is_shipping_cost = search_for_shipping(line)

    # If the cost is listed as a quantity or hourly rate, find the cost
    ea_cost = find_ea_cost(text)
    hr_cost = find_hr_cost(text)

    # Case: Payment line is a labor cost
    if is_labor_cost:
        if ea_cost > -1:
            invoice.labor_cost += ea_cost
            invoice.subtotal += ea_cost
            if __debug__:
                print_to_debug_file(
                    f"Line {curr_line_num}: Adding LABOR COST of:    ${ea_cost}"
                )
        elif hr_cost > -1:
            invoice.labor_cost += hr_cost
            invoice.subtotal += hr_cost
            if __debug__:
                print_to_debug_file(
                    f"Line {curr_line_num}: Adding LABOR COST of:    ${hr_cost}"
                )

    # Case: Payment line is a shipping cost
    elif is_shipping_cost:
        if ea_cost > -1:
            invoice.shipping_cost += ea_cost
            invoice.subtotal += ea_cost
            if __debug__:
                print_to_debug_file(
                    f"Line {curr_line_num}: Adding SHIPPING COST of:    ${ea_cost}"
                )
        elif hr_cost > -1:
            invoice.shipping_cost += hr_cost
            invoice.subtotal += hr_cost
            if __debug__:
                print_to_debug_file(
                    f"Line {curr_line_num}: Adding SHIPPING COST of:    ${hr_cost}"
                )

    # Case: Payment line is a material cost
    else:
        if ea_cost > -1:
            invoice.material_cost += ea_cost
            invoice.subtotal += ea_cost
            if __debug__:
                print_to_debug_file(
                    f"Line {curr_line_num}: Adding MATERIAL COST of:    ${ea_cost}"
                )
        elif hr_cost > -1:
            invoice.material_cost += hr_cost
            invoice.subtotal += hr_cost
            if __debug__:
                print_to_debug_file(
                    f"Line {curr_line_num}: Adding MATERIAL COST of:    ${hr_cost}"
                )

    return invoice


# find_ea_cost searches the payment_lines for any listing of cost listed in quantity
# params: payment_lines: str, the lines of text that make up the payment line
# returns: double, the cost if found, -1 if otherwise
def find_ea_cost(payment_lines):

    for line in payment_lines.splitlines():
        cost = search_payment_line(line, "[0-9]+ea(.*)")
        if cost > -1:
            return cost

    return -1


# find_ea_cost searches the payment_lines for any listing of cost listed in quantity
# params: payment_lines: str, the lines of text that make up the payment line
# returns: double, the cost if found, -1 if otherwise
def find_hr_cost(payment_lines):

    for line in payment_lines.splitlines():
        cost = search_payment_line(line, "[0-9]+hr(.*)")
        if cost > -1:
            return cost

    return -1


# process_end_of_invoice takes the ending of the invoice starting at "Total:subtotal" and searches for
# the sales tax and the listed total on the invoice
# params: text: str, the invoice page to be processed
# params: startingLine: str, the line at which the end of the invoice starts
# parms: invoice: Invoice, the invoice object to be modified
# returns: Invoice, the invoice that was modified
def process_end_of_invoice(text, startingLine, invoice):

    # Only need to process from the start of the subtotal to the end
    text = text[(text.find(startingLine)) :]

    # Find sales tax and listed total and place into invoice
    invoice.sales_tax = float(text.splitlines()[2].replace("$", "").replace(",", ""))
    invoice.listed_total = float(text.splitlines()[3].replace("$", "").replace(",", ""))

    return invoice


# search_for_labor takes a given payment line and searches it for markers
# that would indicate that this line contains a labor cost
# params: line, str, one line of text from the purchase table
# returns: True if a labor cost, False otherwise
def search_for_labor(line):

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


def search_for_shipping(line):

    if ("DELIVERY" in line) or ("UPS GROUND" in line) or ("FREIGHT OUT" in line):
        return True

    return False


# find_payment_terms takes the invoice and searches for an occurance of any
# of the possible payment terms
# params: text: str, the invoice to be searched
# params: payment_terms: list, contains all possible payment terms
# returns: str, payment term if match found, "Could Not Find" otherwise
def find_payment_terms(text, payment_terms):

    # Search for each possible payment term
    for term in payment_terms:
        res = re.search(term, text)

        # If found, return the term
        if res:
            return term

    return "Could Not Find"


# find_sales_rep takes the invoice and searched for the sales rep listed
# params: text: str, the invoice to be saerched
# params: sales_reps: dict, contains all possible sales rep codes and names
# returns: str, the name of the sales rep if found, "Could Not Find" otherwise
def find_sales_rep(text, sales_reps):

    # Search for each possible sales rep
    for key, val in sales_reps.items():
        res = re.search(key, text)

        # If found, return sales rep name
        if res:
            return val

    return "Could Not Find"


# get_filename_from_filepath takes a full filepath to an invoice PDF file and
# isolates the name of the file
# params: str: filepath, the full path to the invoice pdf
# returns: the filename "xxxx.pdf" if found, -1 if not found
def get_filename_from_filepath(filepath):
    res = re.search("SO-(.+).pdf", filepath)

    if res:
        return res.group()
    else:
        return -1
