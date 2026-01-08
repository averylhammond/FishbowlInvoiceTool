from source.InvoiceAppController import InvoiceAppController

# Entry Point
if __name__ == "__main__":
    """
    Entry point to the application. Initializes the InvoiceAppController and starts the application.
    """

    # Create the InvoiceProcessor instance
    invoice_processor = InvoiceAppController()

    # Start the Invoice Processor App
    invoice_processor.start_application()
