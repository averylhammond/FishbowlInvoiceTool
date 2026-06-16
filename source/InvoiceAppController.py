# Import necessary classes from modules
import threading
from pathlib import Path

from source.gui.InvoiceAppDisplay import InvoiceAppDisplay
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.InvoiceProcessor import InvoiceProcessor
from source.ArgumentProvider import ArgumentProvider
from source.SettingsRepository import SettingsRepository
from source.UpdateChecker import UpdateChecker
from source.Invoice import Invoice
from source.constants import (
    COST_CRITERIA_PATH,
    PAYMENT_TERMS_PATH,
    SALES_REPS_PATH,
)

# TODO: See if there is a good logging method to add for debugging


# InvoiceAppController class to drive logic for processing invoice PDFs.
class InvoiceAppController:

    ###########################################################################
    ###                 InvoiceAppController -> __init__()                  ###
    ###########################################################################
    def __init__(self):
        """
        Initializes the InvoiceAppController object

        This includes initializing the File IO Controller, Invoice Processor,
        and GUI Display
        """

        # Argument provider to check for integration test mode
        self.argument_provider = ArgumentProvider()

        # Create File IO Controller, which reads its file paths from source.constants
        self.file_io_controller = InvoiceAppFileIO()

        # Create InvoiceProcessor, provide it with the File IO Controller and criteria for processing invoices
        self.invoice_processor = InvoiceProcessor(
            file_io_controller=self.file_io_controller,
            labor_criteria=self.file_io_controller.labor_criteria,
            labor_exclusions=self.file_io_controller.labor_exclusions,
            shipping_criteria=self.file_io_controller.shipping_criteria,
        )

        # Create the Settings Repository and load the user's persisted settings so
        # they can be handed to the display and restored on startup.
        self.settings_repository = SettingsRepository()
        saved_settings = self.settings_repository.get_all_settings()

        # Create the InvoiceAppDisplay GUI, providing it with the callbacks it
        # needs: processing invoices, reading a file's contents for the native
        # editor/viewer windows, saving edited config files, and persisting user
        # settings. The saved settings restore the user's last theme/font choices.
        self.display = InvoiceAppDisplay(
            title="Invoice Processor",
            window_resolution="750x750",
            process_callback=self.handle_process_invoice,
            read_file_callback=self.file_io_controller.read_text_file,
            save_config_callback=self.handle_save_config,
            save_settings_callback=self.handle_save_setting,
            copy_invoice_callback=self.file_io_controller.copy_invoice_file,
            settings=saved_settings,
        )

        # Wire the GUI's error popup into the File IO Controller and Settings
        # Repository so file/database failures surface to the user without coupling
        # those components to the GUI. This must happen before the config files are
        # parsed below so parse failures can be reported.
        self.file_io_controller.report_error = self.display.show_error_popup
        self.settings_repository.report_error = self.display.show_error_popup

        # Use the File IO Controller to read in the criteria/exclusions for each cost section
        self.file_io_controller.parse_cost_criteria_file()

        # Build payment terms dictionary containing all possible sales rep name codes that could appear on an invoice
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

        # Build sales_rep dictionary containing all possible payment terms that could appear on an invoice
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()

    ###########################################################################
    ###             InvoiceAppController -> start_application()             ###
    ###########################################################################
    def start_application(self):
        """
        Starts the application by entering the tkinter main GUI loop

        Note: If the application is running in integration test mode, the GUI loop is not started,
        and the application is instead directed to process all invoices directly.
        """

        # Reset text files before starting the application
        if __debug__:
            self.file_io_controller.reset_debug_file()

        self.file_io_controller.reset_results_file()

        if self.argument_provider.integration_test_mode:
            # If in integration test mode, process all invoices directly without starting the GUI
            self.display.handle_process_all_invoices()
        else:
            # Kick off a background check for a newer release before entering the
            # GUI loop. Confined to this branch so integration-test mode performs no
            # network I/O.
            self._start_update_check()

            # Else, normally start the GUI application
            self.display.mainloop()

    ###########################################################################
    ###            InvoiceAppController -> _start_update_check()            ###
    ###########################################################################
    def _start_update_check(self):
        """
        Spawns a daemon thread that checks for a newer release on startup.

        Running on a background thread keeps the GUI from blocking while waiting on
        the GitHub API, and the daemon flag ensures a slow or stalled request can
        never delay application shutdown.
        """

        threading.Thread(target=self._run_update_check, daemon=True).start()

    ###########################################################################
    ###             InvoiceAppController -> _run_update_check()             ###
    ###########################################################################
    def _run_update_check(self):
        """
        Worker-thread body for the startup update check.

        Performs the (blocking, but silent-on-failure) update check off the GUI
        thread, then hands the result back to the tkinter main thread via
        display.after() so the GUI is only ever touched from the GUI thread.
        """

        result = UpdateChecker().check_for_update()
        self.display.after(0, self._handle_update_result, result)

    ###########################################################################
    ###            InvoiceAppController -> _handle_update_result()          ###
    ###########################################################################
    def _handle_update_result(self, result):
        """
        Handles the outcome of the startup update check on the GUI thread.

        Triggers the GUI response only when a strictly newer release exists. Does
        nothing when the check failed silently (result is None) or the running
        build is already up to date, so the user is never interrupted.

        Args:
            result (UpdateCheckResult | None): The comparison outcome from
                UpdateChecker.check_for_update(), or None if the check failed.
        """

        if result and result.update_available:
            self.display.show_update_available(result)

    ###########################################################################
    ###          InvoiceAppController -> handle_process_invoice()           ###
    ###########################################################################
    def handle_process_invoice(self, invoice_filepath: Path, append_output: bool):
        """
        Directs components to process the invoice located at invoice_filepath

        Args:
            invoice_filepath (Path): The filepath of the invoice PDF to be processed.
            append_output (bool): Whether to append the Invoice outputs to any existing outputs.
                                    True: append to existing results.txt and output box
                                    False: overwrite existing results.txt and output box
        """

        invoice = Invoice()

        # Command the File IO Controller to read in the invoice located at invoice_filepath
        invoice.page_contents = self.file_io_controller.read_invoice_file(
            invoice_filepath=invoice_filepath
        )

        # If there are no pages in the invoice, show an error and return early
        if not invoice.page_contents or invoice.page_contents[0] is None:
            self.display.show_error_popup(
                error_title="Error",
                error_message=f"No pages were found in the invoice PDF located at {invoice_filepath}.",
            )
            return

        # Print results of reading invoice to debug.txt if in debug mode
        self.file_io_controller.print_to_debug_file(
            f"Processing invoice: {invoice_filepath} with {len(invoice.page_contents)} pages."
        )

        # Populate other initial fields of the invoice from the first page of the PDF
        self.invoice_processor.populate_invoice(
            invoice=invoice,
            sales_reps=self.sales_reps,
            payment_terms=self.payment_terms,
        )

        # Forward call to the Invoice Processor
        self.invoice_processor.process_invoice(invoice=invoice)

        # Display the calculated totals in the GUI
        self.display.display_invoice_output(
            invoice=invoice, append_output=append_output
        )

        # Invoices generated by Fishbowl are known to have rounding errors, likely due to floating point precision issues, so
        # we need to account for that and let the user know that the generated total may not match the listed total on the invoice.
        # This is done by displaying an error popup window
        if invoice.total != invoice.listed_total:
            self.display.show_error_popup(
                error_title="Calculated Total Mismatch",
                error_message=f"The calculated total of ${invoice.total} does not match the listed total of ${invoice.listed_total} for invoice {invoice.order_number}.",
            )

        # Print calculated invoice output to results.txt
        self.file_io_controller.print_invoice_to_output_file(
            invoice=invoice, append_output=append_output
        )

        # Print completion notice to debug.txt if in debug mode
        self.file_io_controller.print_to_debug_file(
            contents=f"Processed all sales for invoice: {invoice_filepath}\n"
        )

    ###########################################################################
    ###            InvoiceAppController -> handle_save_config()             ###
    ###########################################################################
    def handle_save_config(self, config_path: Path, contents: str):
        """
        Persists edited config file contents to disk, then re-parses that config
        so the changes take effect in the running application without a restart.

        Args:
            config_path (Path): The config file being saved
            contents (str): The new contents to write to the config file
        """

        # Write the edited contents to disk
        self.file_io_controller.write_text_file(
            file_path=config_path, contents=contents
        )

        # Map each config file to the action that reloads it into memory. Using a
        # dispatch dict keeps this open to new config files without growing an
        # if/elif chain.
        reloaders = {
            COST_CRITERIA_PATH: self._reload_cost_criteria,
            PAYMENT_TERMS_PATH: self._reload_payment_terms,
            SALES_REPS_PATH: self._reload_sales_reps,
        }

        # Reload the config that was just saved, if it is one we manage
        reloader = reloaders.get(config_path)
        if reloader:
            reloader()

    ###########################################################################
    ###            InvoiceAppController -> handle_save_setting()            ###
    ###########################################################################
    def handle_save_setting(self, key: str, value: str):
        """
        Persists a single user setting so it is restored on the next launch.

        Args:
            key (str): The setting's identifier (e.g. "theme", "font_family")
            value (str): The setting's value to store
        """

        self.settings_repository.save_setting(key=key, value=value)

    ###########################################################################
    ###           InvoiceAppController -> _reload_cost_criteria()           ###
    ###########################################################################
    def _reload_cost_criteria(self):
        """
        Re-parses the cost criteria config into the File IO Controller's criteria
        lists (cleared and repopulated in place, so the InvoiceProcessor's
        references stay valid).
        """
        self.file_io_controller.parse_cost_criteria_file()

    ###########################################################################
    ###           InvoiceAppController -> _reload_payment_terms()           ###
    ###########################################################################
    def _reload_payment_terms(self):
        """
        Re-parses the payment terms config into the controller's payment_terms list
        """
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

    ###########################################################################
    ###            InvoiceAppController -> _reload_sales_reps()             ###
    ###########################################################################
    def _reload_sales_reps(self):
        """
        Re-parses the sales reps config into the controller's sales_reps dictionary
        """
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()
