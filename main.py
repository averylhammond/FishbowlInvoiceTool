from source.InvoiceAppController import InvoiceAppController

# TODO: Add a /scripts folder to automate PyInstaller process for new release packages

# Entry Point
if __name__ == "__main__":

    # Create the InvoiceProcessor instance
    invoice_processor = InvoiceAppController()

    # Start the Invoice Processor App
    invoice_processor.start_application()
