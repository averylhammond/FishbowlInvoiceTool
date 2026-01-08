import argparse


# ArgumentProvider class to provide script arguments to any module that needs them
class ArgumentProvider:

    def __init__(self):
        """
        Initializes the ArgumentProvider object

        This includes parsing command line arguments to determine application settings
        """

        # Define an integration test mode, default to False unless specified by --integration-test flag
        self.integration_test_mode = False

        self.parse_arguments()

    def parse_arguments(self):
        """
        Parses command line arguments and stores them as attributes of the object.
        """

        # Parse arguments to find out if we are running in integration test mode
        parser = argparse.ArgumentParser(description="Invoice Processor Application")
        parser.add_argument(
            "--integration-test",
            action="store_true",
            help="Run the application in integration test mode.",
        )
        args = parser.parse_args()

        # Store the integration test mode flag
        self.integration_test_mode = args.integration_test
