from re import search
from decimal import Decimal, ROUND_HALF_UP

from source.globals import *


def search_text_by_re(text: str, regex: str) -> str:
    """
    Takes a given regex and searches the text for a match

    Args:
        text (str): The text to be searched
        regex (str): The regex to be matched

    Returns:
        str: The matched string if found, empty string otherwise
    """
    res = search(pattern=regex, string=text)
    if res:
        return res.group()
    else:
        return str()


def search_payment_line(line: str, regex: str) -> Decimal:
    """
    Takes a given regex and searches the line for a match. Then does
    special handling to extract the payment amount from the line

    Args:
        line (str): One line of text from the purchase table
        regex (str): Regex to be matched

    Returns:
        Decimal: The payment amount as a Decimal if match found, 0.0 otherwise
    """

    res = search(pattern=regex, string=line)

    if res:
        return format_currency((res.group().split()[2]).replace(",", ""))
    else:
        return DECIMAL_ZERO


def find_payment_terms(text: str, payment_terms: list) -> str:
    """
    Searches text for an occurrence of any of the possible payment terms

    Args:
        text (str): The text to be searched
        payment_terms (list): Contains all possible payment terms

    Returns:
        str: The payment term if found, empty string otherwise
    """

    # Search for each possible payment term
    for term in payment_terms:
        res = search(pattern=term, string=text)

        # If found, return the term
        if res:
            return term

    # If no payment term was found, return empty string
    return str()


def find_sales_rep(text: str, sales_reps: dict) -> str:
    """
    Searches the text for an occurrence of any of the possible sales reps

    Args:
        text (str): The text to be searched
        sales_reps (dict): Contains all possible sales rep codes and names

    Returns:
        str: The name of the sales rep if found, empty string otherwise
    """

    # Search for each possible sales rep
    for key, val in sales_reps.items():
        res = search(pattern=key, string=text)

        # If found, return sales rep name
        if res:
            return val

    return str()


def format_currency(value) -> Decimal:
    """
    Takes a string representation of a currency value and formats it
    to a Decimal with two decimal places, rounding half up

    Args:
        value (any): The string representation of the currency value

    Returns:
        Decimal: The formatted currency value
    """
    return Decimal(str(value)).quantize(
        exp=Decimal("0.01"), rounding=ROUND_HALF_UP
    )
