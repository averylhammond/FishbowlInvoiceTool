from search import *
import logging


# Invoice class to hold all attributes of the invoice that must be
# passes to QuickBooks API
class Invoice:
    def __init__(self):
        self.customer = None  # Name of customer on invoice
        self.date = None  # Date of invoice
        self.invoiceNum = None  # Invoice number, as S12345
        self.poNum = None  # PO Number
        self.paymentTerms = None  # Listed payment terms
        self.rep = None  # Sales rep identifier
        self.laborCost = 0.0  # Total cost of labor
        self.materialCost = 0.0  # Total cost of material
        self.shippingCost = 0.0  # Total cost of shipping
        self.subTotal = 0.0  # Subtotal, from summing all costs
        self.salesTax = 0.0  # Additional sales tax
        self.total = 0.0  # Calculated as subtotal plus salesTax
        self.listedTotal = 0.0  # Total as listed on the invoice

    # populateInvoice initializes the appropriate fields of a given Invoice object
    # params: text: str taken from the first page of the invoice
    # params: allSalesReps: dict, all possible sales rep codes and names
    # params: allPaymentTerms: list, all possible payment terms
    # returns: N/A
    def populateInvoice(self, text, allSalesReps, allPaymentTerms):
        self.invoiceNum = searchInvoice(text, "S(\d{5})")
        self.date = searchInvoice(text, "\d{2}/\d{2}/\d{4}")
        self.customer = searchInvoice(text, "Customer: .+").replace("Customer: ", "")
        self.poNum = (searchInvoice(text, "PO Number: .+S")[:-1]).replace(
            "PO Number: ", ""
        )
        self.paymentTerms = findPaymentTerms(text, allPaymentTerms)
        self.rep = findSalesRep(text, allSalesReps)

    # dumpInvoice dumps all fields of a given invoice to the terminal for debugging
    # params: N/A
    # returns: N/A
    def dumpInvoice(self):
        logging.debug(
            "\n***********************************\nDumping Invoice Contents!"
        )
        logging.debug(f"Customer: {self.customer}")
        logging.debug(f"Date: {self.date}")
        logging.debug(f"Invoice Number: {self.invoiceNum}")
        logging.debug(f"PO Number: {self.poNum}")
        logging.debug(f"Payment Terms: {self.paymentTerms}")
        logging.debug(f"Rep: {self.rep}")
        logging.debug(f"Labor Costs: ${round(self.laborCost, 2)}")
        logging.debug(f"Material Costs: ${round(self.materialCost, 2)}")
        logging.debug(f"Shipping Costs: ${round(self.shippingCost, 2)}")
        logging.debug(f"SubTotal: ${round(self.subTotal, 2)}")
        logging.debug(f"Sales Tax: ${round(self.salesTax, 2)}")
        logging.debug(f"Calculated Total: ${round(self.total, 2)}")
        logging.debug(f"Listed Total: ${round(self.listedTotal, 2)}")
        logging.debug("***********************************")

    # calculateTotal calculates the total for a fully processed invoice
    # params: N/A
    # returns: N/A
    def calculateTotal(self):
        self.total = self.subTotal + self.salesTax
