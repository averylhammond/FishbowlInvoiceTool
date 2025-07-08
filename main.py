import logging
from source.InvoiceProcessor import InvoiceProcessor


# Entry Point
if __name__ == "__main__":

    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG, format="[%(levelname)s] %(asctime)s - %(message)s"
    )

    # Create the InvoiceProcessor instance
    invoice_processor = InvoiceProcessor()

    # Start the Invoice Processor App
    invoice_processor.start()
