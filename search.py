import re
from fio import *

# searchInvoice takes a given regex and searches the invoice for a match
# params: text: str, first page of the invoice
# params: regex: str, regex to be matched
# returns: Either returns the str match of the regex if successful, or None
def searchInvoice(text, regex):
    res = re.search(regex, text)
    
    if res:
        return res.group()
    else:
        return None
    

# searchPaymentLine takes a given regex and searches one line of payment text
# from the purchase table of the invoice
# params: line: str, one line of text from the purchase table
# params: regex: str, regex to be matched
# returns: N/A
def searchPaymentLine(line, regex):
    res = re.search(regex, line)

    if res:
        return float((res.group().split()[2]).replace(',', ''))
    else:
        return -1
    

# processPaymentLine takes a given line from the payment table and processes it. This includes 
# reading the entire row, determining if the payment line refers to a labor, shipping, or 
# material cost, and find the cost. It then adds that cost to the invoice total
# params: text: str, the current page of the invoice
# params: line: str, the line at which the payment line starts
# params: invoice: Invoice, the invoice struct to be modified
# params: currLineNum: int, the current payment line number being processed
# returns: Invoice, the invoice that was modified
def processPaymentLine(text, line, invoice, currLineNum):
    
    # If this line contains a subtotal, do nothing
    if "Subtotal" in line:
        return invoice

    # Only take the current payment line, remove everything before line,
    # and everything right after the next payment line
    text = text[(text.find(line)):]
    text = text[:text.find(f"\n{currLineNum+1} ")]

    # Determine if the payment line is a labor, shipping, or material cost
    isLaborCost = searchForLabor(line)
    isShippingCost = searchForShipping(line)

    # If the cost is listed as a quantity or hourly rate, find the cost
    eaCost = findEaCost(text)
    hrCost = findHrCost(text)

    # Case: Payment line is a labor cost
    if isLaborCost:
        if eaCost > -1:
            invoice.laborCost += eaCost
            invoice.subTotal += eaCost
            if __debug__:
                printToDebugFile(f"Line {currLineNum}: Adding LABOR COST of:    ${eaCost}")
        elif hrCost > -1:
            invoice.laborCost += hrCost
            invoice.subTotal += hrCost
            if __debug__:
                printToDebugFile(f"Line {currLineNum}: Adding LABOR COST of:    ${hrCost}")

    # Case: Payment line is a shipping cost
    elif isShippingCost:
        if eaCost > -1:
            invoice.shippingCost += eaCost
            invoice.subTotal += eaCost
            if __debug__:
                printToDebugFile(f"Line {currLineNum}: Adding SHIPPING COST of:    ${eaCost}")
        elif hrCost > -1:
            invoice.shippingCost += hrCost
            invoice.subTotal += hrCost
            if __debug__:
                printToDebugFile(f"Line {currLineNum}: Adding SHIPPING COST of:    ${hrCost}")

    # Case: Payment line is a material cost
    else:
        if eaCost > -1:
            invoice.materialCost += eaCost
            invoice.subTotal += eaCost
            if __debug__:
                printToDebugFile(f"Line {currLineNum}: Adding MATERIAL COST of:    ${eaCost}")
        elif hrCost > -1:
            invoice.materialCost += hrCost
            invoice.subTotal += hrCost
            if __debug__:
                printToDebugFile(f"Line {currLineNum}: Adding MATERIAL COST of:    ${hrCost}")

    return invoice

# findEaCost searches the paymentLines for any listing of cost listed in quantity
# params: paymentLines: str, the lines of text that make up the payment line
# returns: double, the cost if found, -1 if otherwise
def findEaCost(paymentLines):

    for line in paymentLines.splitlines():
        cost = searchPaymentLine(line, "[0-9]+ea(.*)")
        if cost > -1:
            return cost
        
    return -1


# findEaCost searches the paymentLines for any listing of cost listed in quantity
# params: paymentLines: str, the lines of text that make up the payment line
# returns: double, the cost if found, -1 if otherwise
def findHrCost(paymentLines):
    
    for line in paymentLines.splitlines():
        cost = searchPaymentLine(line, "[0-9]+hr(.*)")
        if cost > -1:
            return cost
        
    return -1
    

# processEndOfInvoice takes the ending of the invoice starting at "Total:Subtotal" and searches for
# the sales tax and the listed total on the invoice
# params: text: str, the invoice page to be processed
# params: startingLine: str, the line at which the end of the invoice starts
# parms: invoice: Invoice, the invoice object to be modified
# returns: Invoice, the invoice that was modified
def processEndOfInvoice(text, startingLine, invoice):

    # Only need to process from the start of the subtotal to the end
    text = text[(text.find(startingLine)):]

    # Find sales tax and listed total and place into invoice
    invoice.salesTax = float(text.splitlines()[2].replace('$', '').replace(',', ''))
    invoice.listedTotal = float(text.splitlines()[3].replace('$', '').replace(',', ''))

    return invoice

# searchForLabor takes a given payment line and searches it for markers
# that would indicate that this line contains a labor cost
# params: line, str, one line of text from the purchase table
# returns: True if a labor cost, False otherwise
def searchForLabor(line):
    
    # Only return true is MF/ or MD/ was found in the line. Does not include
    # MF/RHR or MF/LHR or MD/RHR or MD/LHR
    if ((("MF/" in line) or ("MD/" in line)) and 
        (("MF/RHR" not in line) and ("MF/LHR" not in line) and 
         ("MD/RHR" not in line) and ("MD/LHR" not in line))):
        return True
    else:
        return False

def searchForShipping(line):

    if (("DELIVERY" in line) or ("UPS GROUND" in line)
        or ("FREIGHT OUT" in line)):
        return True

    return False

# findPaymentTerms takes the invoice and searches for an occurance of any
# of the possible payment terms
# params: text: str, the invoice to be searched
# params: allPaymentTerms: list, contains all possible payment terms
# returns: str, payment term if match found, "Could Not Find" otherwise
def findPaymentTerms(text, allPaymentTerms):

    # Search for each possible payment term
    for term in allPaymentTerms:
        res = re.search(term, text)

        # If found, return the term
        if res:
            return term
        
    return "Could Not Find"


# findSalesRep takes the invoice and searched for the sales rep listed
# params: text: str, the invoice to be saerched
# params: allSalesReps: dict, contains all possible sales rep codes and names
# returns: str, the name of the sales rep if found, "Could Not Find" otherwise
def findSalesRep(text, allSalesReps):

    # Search for each possible sales rep
    for key, val in allSalesReps.items():
        res = re.search(key, text)

        # If found, return sales rep name
        if res:
            return val
        
    return "Could Not Find"


# getFilenameFromFilepath takes a full filepath to an invoice PDF file and 
# isolates the name of the file
# params: str: filepath, the full path to the invoice pdf
# returns: the filename "xxxx.pdf" if found, -1 if not found
def getFilenameFromFilepath(filepath):
    res = re.search("SO-(.+).pdf", filepath)

    if res:
        return res.group()
    else:
        return -1