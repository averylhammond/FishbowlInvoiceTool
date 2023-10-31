import os

# resetDebugFile deletes debug.txt that was created from the previous program execution
# params: N/A
# returns: N/A
def resetDebugFile():
    if os.path.isfile("./debug.txt"):
        os.remove("./debug.txt")


# resetOutputFile deletes results.txt that was created from the previous program execution
# params: N/A
# returns: N/A
def resetOutputFile():
    if os.path.isfile("./results.txt"):
        os.remove("./results.txt")


# printToDebugFile writes the str contents to debug.txt
# params: contents: str, the contents to be written to file
# returns: N/A
def printToDebugFile(contents):
    
    # If debug.txt already exists, append to it, otherwise write from beginning
    if os.path.isfile("./debug.txt"):
        writeOrAppend = 'a'
    else:
        writeOrAppend = 'w'

    # Write contents to file
    with open("debug.txt", writeOrAppend) as f:
        f.write(contents + "\n")


# printToOutputFile writes each field of the invoice object to results.txt
# params: invoice: Invoice object, the invoice whose fields are to be output
# returns: N/A
def printToOutputFile(invoice):
    
    # If results.txt already exists, append to it, otherwise write from beginning
    if os.path.isfile("./results.txt"):
        writeOrAppend = 'a'
    else:
        writeOrAppend = 'w'

    # Write invoice contents to file
    with open("results.txt", writeOrAppend) as f:
        f.write("***********************************\n")
        f.write(f"Processed Invoice Results:\n")
        f.write(f"Customer Name:    {invoice.customer}\n")
        f.write(f"Invoice Date:     {invoice.date}\n")
        f.write(f"Invoice Number:   {invoice.invoiceNum}\n")
        f.write(f"PO Number:        {invoice.poNum}\n")
        f.write(f"Payment Terms:    {invoice.paymentTerms}\n")
        f.write(f"Sales Rep:        {invoice.rep}\n")
        f.write(f"Labor Cost:       ${round(invoice.laborCost, 2)}\n")
        f.write(f"Material Cost:    ${round(invoice.materialCost, 2)}\n")
        f.write(f"Shipping Cost:    ${round(invoice.shippingCost, 2)}\n")
        f.write(f"Subtotal:         ${round(invoice.subTotal, 2)}\n")
        f.write(f"Sales Tax:        ${round(invoice.salesTax, 2)}\n")
        f.write(f"Calculated Total: ${round(invoice.total, 2)}\n")
        f.write(f"Listed Total:     ${round(invoice.listedTotal, 2)}\n")
        f.write("***********************************\n")


# buildDictSalesReps builds the salesReps dictionary that contains the
# invoice code and matching name for each sales rep as defined in Configs/salesReps.txt
# params: N/A
# returns: dict, the populated dictionary with all codes as keys and names as values
def buildDictSalesReps():
    
    with open("Configs/salesReps.txt", 'r') as f:
        dict = {}

        # Search through text file, only take non-comment entries
        for line in f:
            if line[0] != '*':
                res = line.partition('=')
                dict[res[0]] = res[2].replace('\n', '')  # Strip '\n' from all entries
        
    return dict

# buildListPaymentTerms builds the paymentTerms list that contains each possible
# payment term as defined in Configs/paymentTerms.txt
# params: N/A
# returns: list, contains each possible payment term that could be found in the invoice
def buildListPaymentTerms():
    
    with open("Configs/paymentTerms.txt", 'r') as f:
        list = []

        # Search through text file, only take non-comment entries
        for line in f:
            if line[0] != '*':
                list.append(line.replace('\n','')) # Strip '\n' from all entries

    return list
