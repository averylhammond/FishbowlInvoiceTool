import logging
from source.InvoiceAppController import InvoiceAppController


# Entry Point
if __name__ == "__main__":

    # TODO: Only do this in debug configuration?
    # # Setup logging
    logging.basicConfig(
        level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s"
    )

    # Create the InvoiceProcessor instance
    invoice_processor = InvoiceAppController()

    # Start the Invoice Processor App
    invoice_processor.start_application()
