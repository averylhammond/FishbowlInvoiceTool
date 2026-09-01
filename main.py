"""
Entry point to the application. Initializes the InvoiceAppController and starts
the application.
"""

from source.InvoiceAppController import InvoiceAppController

# Entry Point
if __name__ == "__main__":
    # Create the InvoiceAppController instance
    controller = InvoiceAppController()

    # Start the Invoice Processor App
    controller.start_application()
