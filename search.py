import re

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
    

# searchForLabor takes a given payment line and searches it for markers
# that would indicate that this line contains a labor cost
# params: line, str, one line of text from the purchase table
# returns: True if a labor cost, False otherwise
def searchForLabor(line):
    
    # Only return true is MF/ or MD/ was found in the line. Does not include
    # MF/RHR or MF/LHR or MD/RHR or MD/LHR
    if (("MF/" in line) or ("MD/" in line)) and (("MF/RHR" not in line) and ("MF/LHR" not in line) and ("MD/RHR" not in line) and ("MD/LHR" not in line)):
        return True
    else:
        return False

# searchForSalesTax takes a given line and searches it for the listed sales tax
# params: line: str, the line of text to be searched
# returns: True if sales tax found, otherwise False
def searchForSalesTax(line):
    res = re.search("Sales Tax:", line)

    if res:
        return True
    else:
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