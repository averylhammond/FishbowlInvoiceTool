import PyPDF2, re, logging, os, win32gui, win32con
import PySimpleGUI as sg
from search import *
from invoice import *
from fio import *
from gui import *

# Uncomment these lines when running pyinstaller to hide the windows terminal
# upon program execution
hide = win32gui.GetForegroundWindow()
win32gui.ShowWindow(hide, win32con.SW_HIDE)

# Find all possible sales reps and payment terms, built from "Config" folder
allSalesReps = buildDictSalesReps()
allPaymentTerms = buildListPaymentTerms()


# processInvoice is the main function that process the invoice pdf
# params: invoicePath: str, path to invoice pdf file to be processed
# params: filename: str, the name of the file to be processed
# params: allSalesReps, dict, contains all possible sales rep codes as keys
#         and names as value
# params: allPaymentTerms: list, contains all possible payment terms
# returns: N/A
def processInvoice(invoicePath, filename):

    # Read text from input PDF
    pdf = PyPDF2.PdfReader(invoicePath)

    # Get Number of Pages
    numPages = len(pdf.pages)

    if __debug__:
        printToDebugFile(f"\nProcessing file: {filename}")
        printToDebugFile(f"Number of Pages in invoice: {numPages}")

    # Process First Page
    currPage = pdf.pages[0]
    text = currPage.extract_text()

    # Create Invoice object and populate initial fields
    invoice = Invoice()
    invoice.populateInvoice(text, allSalesReps, allPaymentTerms)

    # Keep track of next expected payment line number
    nextLineNum = 1

    # Loop through each page to read purchase table
    for i in range(1, numPages + 1):

        if __debug__:
            printToDebugFile(f"Processing sales on page {i}")

        # If not on first page, extract text from new page
        if i > 1:
            currPage = pdf.pages[i - 1]
            text = currPage.extract_text()

        # At this point, can disregard everything before the purchase table
        # Trim off everything before purchase table (before the line Ordered Total Price)
        if len(text[(text.find("Ordered Total Price")) :]) > 1:
            text = text[(text.find("Ordered Total Price")) :]

        # Loop through each line in the table. Some table entries may have multiple lines that need
        # to be processed
        for line in text.splitlines():

            # Check if at beginning of the line in the table. If so, process this payment item
            if line.startswith(f"{nextLineNum} "):
                invoice = processPaymentLine(text, line, invoice, nextLineNum)
                nextLineNum += 1  # Update nextLineNum

            # "Total:Subtotal" is the beginning of the end of the invoice
            if "Total:Subtotal" in line:
                invoice = processEndOfInvoice(text, line, invoice)

    if __debug__:
        printToDebugFile("Finished processing sales on current invoice!")

    # Calculate total from subtotal and sales tax
    invoice.calculateTotal()

    # Print output to results.txt
    printToOutputFile(invoice)

    # invoice.dumpInvoice()
    return invoice


# updateInvoiceGui is the handler for the process button being pressed from the GUI. It
# takes thefilepath that was input and runs the processInvoice function and returns the output
# params: invoicePath, str, the full file path the invoice to be processed
# returns: str, output of results.txt to be displayed on the "output" GUI element
def updateInvoiceGui(invoicePath):

    # If an empty path was given, ask for valid input
    if invoicePath == "":
        return ("Please Select a valid Invoice to Process...", 0.0)

    # Clear output file incase previous invoice was listed
    resetOutputFile()
    invoice = processInvoice(invoicePath, getFilenameFromFilepath(invoicePath))

    # Reset diff on each update, then calculate the new diff
    diff = 0.0
    diff = invoice.listedTotal - invoice.total

    # Open output file and read the calculated results to send to the GUI
    with open("results.txt", "r") as f:
        results = f.read()
        return results, diff


# run is the main loop of the program. It builds the GUI and then sits in a while
# True loop and processes invoices as they are selected by the user
# params: N/A
# returns: N/A
def run():

    # Start the GUIs file browser in the Invoices folder
    workingDir = os.getcwd() + "/Invoices"
    output = sg.Text()

    layout = [
        [sg.Text("Choose an invoice PDF to process...")],  # First text window
        [
            sg.InputText(key="-FILE_PATH-"),  # File browser GUI element
            sg.FileBrowse(
                initial_folder=workingDir, file_types=[("PDF Files", "*.pdf")]
            ),
        ],
        [sg.Button("Process This Invoice"), sg.Exit()],  # Exit button
        [output],  # Output text window
    ]

    # Set theme for big style
    sg.theme("TealMono")

    # Create window
    window = sg.Window("Automated Invoice Processor Tool", layout, size=(500, 500))

    # Main program loop
    while True:
        # Read user input from GUI
        event, values = window.read()

        # If exit is pressed, break out of loop and close window
        if event in (sg.WIN_CLOSED, "Exit"):
            break

        # If the process button is selected, process the invoice
        elif event == "Process This Invoice":
            res, diff = updateInvoiceGui(values["-FILE_PATH-"])
            output.update(res)

            # If there is a discrepancy between the listed total and the
            # calculated total, let the user know with a popup window
            if diff != 0.0:
                sg.popup(
                    f"The calculated invoice total was different than the listed invoice total, with a difference of {diff}!"
                )

    # If break, close app
    window.close()


# Entry Point
if __name__ == "__main__":

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s"
    )

    # If running in debug mode, reset debug.txt
    if __debug__:
        resetDebugFile()

    # Reset results.txt
    resetOutputFile()

    # Setup and run the GUI loop
    run()
