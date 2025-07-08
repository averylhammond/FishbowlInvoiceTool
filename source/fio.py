import os


# reset_debug_file deletes debug.txt that was created from the previous program execution
# params: N/A
# returns: N/A
def reset_debug_file():
    if os.path.isfile("./debug.txt"):
        os.remove("./debug.txt")


# reset_output_file deletes results.txt that was created from the previous program execution
# params: N/A
# returns: N/A
def reset_output_file():
    if os.path.isfile("./results.txt"):
        os.remove("./results.txt")


# print_to_debug_file writes the str contents to debug.txt
# params: contents: str, the contents to be written to file
# returns: N/A
def print_to_debug_file(contents):

    # If debug.txt already exists, append to it, otherwise write from beginning
    if os.path.isfile("./debug.txt"):
        write_or_append = "a"
    else:
        write_or_append = "w"

    # Write contents to file
    with open("debug.txt", write_or_append) as f:
        f.write(contents + "\n")


# print_to_output_file writes each field of the invoice object to results.txt
# params: invoice: Invoice object, the invoice whose fields are to be output
# returns: N/A
def print_to_output_file(invoice):

    # If results.txt already exists, append to it, otherwise write from beginning
    if os.path.isfile("./results.txt"):
        write_or_append = "a"
    else:
        write_or_append = "w"

    # Write invoice contents to file
    with open("results.txt", write_or_append) as f:
        f.write("***********************************\n")
        f.write(f"Processed Invoice Results:\n")
        f.write(f"Customer Name:    {invoice.customer_name}\n")
        f.write(f"Invoice Date:     {invoice.date}\n")
        f.write(f"Order Number:     {invoice.order_number}\n")
        f.write(f"PO Number:        {invoice.po_number}\n")
        f.write(f"Payment Terms:    {invoice.payment_terms}\n")
        f.write(f"Sales Rep:        {invoice.sales_rep}\n")
        f.write(f"Labor Cost:       ${round(invoice.labor_cost, 2)}\n")
        f.write(f"Material Cost:    ${round(invoice.material_cost, 2)}\n")
        f.write(f"Shipping Cost:    ${round(invoice.shipping_cost, 2)}\n")
        f.write(f"subtotal:         ${round(invoice.subtotal, 2)}\n")
        f.write(f"Sales Tax:        ${round(invoice.sales_tax, 2)}\n")
        f.write(f"Calculated Total: ${round(invoice.total, 2)}\n")
        f.write(f"Listed Total:     ${round(invoice.listed_total, 2)}\n")
        f.write("***********************************\n")


# build_dict_sales_reps builds the salesReps dictionary that contains the
# invoice code and matching name for each sales rep as defined in Configs/salesReps.txt
# params: sales_reps_filepath: str, the path to the sales reps config file
# returns: dict, the populated dictionary with all codes as keys and names as values
def build_dict_sales_reps(sales_reps_filepath):

    with open(sales_reps_filepath, "r") as f:
        dict = {}

        # Search through text file, only take non-comment entries
        for line in f:
            if line[0] != "*":
                res = line.partition("=")
                dict[res[0]] = res[2].replace("\n", "")  # Strip '\n' from all entries

    return dict


# build_list_payment_terms builds the payment_terms list that contains each possible
# payment term as defined in Configs/payment_terms.txt
# params: payment_terms_filepath: str, the path to the payment terms config file
# returns: list, contains each possible payment term that could be found in the invoice
def build_list_payment_terms(payment_terms_filepath):

    with open(payment_terms_filepath, "r") as f:
        list = []

        # Search through text file, only take non-comment entries
        for line in f:
            if line[0] != "*":
                list.append(line.replace("\n", ""))  # Strip '\n' from all entries

    return list
