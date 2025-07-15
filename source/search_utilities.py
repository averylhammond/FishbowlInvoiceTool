from re import search


# search_text_by_re takes a given regex and searches the text for a match
# param: text: str, text to be searched
# param: regex: str, regex to be matched
# returns: Either returns the str match of the regex if successful, or None
def search_text_by_re(text, regex):
    res = search(regex, text)
    if res:
        return res.group()
    else:
        return None


# search_payment_line takes a given regex and searches text for a match. Then does
# special handling to extract the payment amount from the line
# param: line: str, one line of text from the purchase table
# param: regex: str, regex to be matched
# returns: The payment amount as a float if match found, None otherwise
def search_payment_line(line, regex):
    res = search(regex, line)

    if res:
        return float((res.group().split()[2]).replace(",", ""))
    else:
        return None


# find_payment_terms searches text for an occurance of any
# of the possible payment terms
# param: text: str, the text to be searched
# param: payment_terms: dict, contains all possible payment terms
# returns: str, payment term if match found, None otherwise
def find_payment_terms(text, payment_terms):

    # Search for each possible payment term
    for term in payment_terms:
        res = search(term, text)
        # If found, return the term
        if res:
            return term

    # If no payment term was found, return None
    return None


# find_sales_rep searches text for the any of the possible sales reps
# param: text: str, the text to be searched
# param: sales_reps: dict, contains all possible sales rep codes and names
# returns: str, the name of the sales rep if found, None otherwise
def find_sales_rep(text, sales_reps):

    # Search for each possible sales rep
    for key, val in sales_reps.items():
        res = search(key, text)
        # If found, return sales rep name
        if res:
            return val
    return None
