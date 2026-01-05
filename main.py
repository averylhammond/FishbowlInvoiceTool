from source.InvoiceAppController import InvoiceAppController

# TODO: Add a /scripts folder to automate PyInstaller process for new release packages
# TODO: Update README.md with the newer folder structure
# TODO: Update debug.txt handling so that a fresh clone doesn't error out when one isn't there to begin with
# TODO: Update README.md with instructions for running the unit tests
# TODO: Update code to not need a logs/ folder, create it if not there

# Entry Point
if __name__ == "__main__":

    # Create the InvoiceProcessor instance
    invoice_processor = InvoiceAppController()

    # Start the Invoice Processor App
    invoice_processor.start_application()
