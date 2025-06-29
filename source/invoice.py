from source.search import *
import logging


# Invoice class to hold all attributes of the invoice that must be
# passes to QuickBooks API
class Invoice:
    def __init__(self):
        self.customer = None  # Name of customer on invoice
        self.date = None  # Date of invoice
        self.invoice_num = None  # Invoice number, as S12345
        self.po_num = None  # PO Number
        self.payment_terms = None  # Listed payment terms
        self.rep = None  # Sales rep identifier
        self.labor_cost = 0.0  # Total cost of labor
        self.material_cost = 0.0  # Total cost of material
        self.shipping_cost = 0.0  # Total cost of shipping
        self.subtotal = 0.0  # subtotal, from summing all costs
        self.sales_tax = 0.0  # Additional sales tax
        self.total = 0.0  # Calculated as subtotal plus sales_tax
        self.listed_total = 0.0  # Total as listed on the invoice

    # populate_invoice initializes the appropriate fields of a given Invoice object
    # params: text: str taken from the first page of the invoice
    # params: sales_reps: dict, all possible sales rep codes and names
    # params: payment_terms: list, all possible payment terms
    # returns: N/A
    def populate_invoice(self, text, sales_reps, payment_terms):
        self.invoice_num = search_invoice(text, "S(\d{5})")
        self.date = search_invoice(text, "\d{2}/\d{2}/\d{4}")
        self.customer = search_invoice(text, "Customer: .+").replace("Customer: ", "")
        self.po_num = (search_invoice(text, "PO Number: .+S")[:-1]).replace(
            "PO Number: ", ""
        )
        self.payment_terms = find_payment_terms(text, payment_terms)
        self.rep = find_sales_rep(text, sales_reps)

    # dumpInvoice dumps all fields of a given invoice to the terminal for debugging
    # params: N/A
    # returns: N/A
    def dumpInvoice(self):
        logging.debug(
            "\n***********************************\nDumping Invoice Contents!"
        )
        logging.debug(f"Customer: {self.customer}")
        logging.debug(f"Date: {self.date}")
        logging.debug(f"Invoice Number: {self.invoice_num}")
        logging.debug(f"PO Number: {self.po_num}")
        logging.debug(f"Payment Terms: {self.payment_terms}")
        logging.debug(f"Rep: {self.rep}")
        logging.debug(f"Labor Costs: ${round(self.labor_cost, 2)}")
        logging.debug(f"Material Costs: ${round(self.material_cost, 2)}")
        logging.debug(f"Shipping Costs: ${round(self.shipping_cost, 2)}")
        logging.debug(f"subtotal: ${round(self.subtotal, 2)}")
        logging.debug(f"Sales Tax: ${round(self.sales_tax, 2)}")
        logging.debug(f"Calculated Total: ${round(self.total, 2)}")
        logging.debug(f"Listed Total: ${round(self.listed_total, 2)}")
        logging.debug("***********************************")

    # calculate_total calculates the total for a fully processed invoice
    # params: N/A
    # returns: N/A
    def calculate_total(self):
        self.total = self.subtotal + self.sales_tax
