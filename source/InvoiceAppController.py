# Import necessary classes from modules
from pathlib import Path

from fishbowl_common import (
    ArgumentProvider,
    PatchNotes,
    SettingsRepository,
    UpdateCoordinator,
    compare_versions,
)

from source.constants import (
    APP_NAME,
    COST_CRITERIA_PATH,
    GITHUB_REPO,
    INSTALLER_ASSET_PATTERN,
    PATCH_NOTES_PATH,
    PAYMENT_TERMS_PATH,
    SALES_REPS_PATH,
    SETTING_KEY_LAST_SEEN_VERSION,
    SETTINGS_DB_PATH,
    VERSION,
)
from source.gui.InvoiceAppDisplay import InvoiceAppDisplay
from source.Invoice import Invoice
from source.InvoiceAppFileIO import InvoiceAppFileIO
from source.InvoiceProcessor import InvoiceProcessor

# TODO: See if there is a good logging method to add for debugging


# InvoiceAppController class to drive logic for processing invoice PDFs.
class InvoiceAppController:

    ###########################################################################
    ###                 InvoiceAppController -> __init__()                  ###
    ###########################################################################
    def __init__(self) -> None:
        """
        Initializes the InvoiceAppController object

        This includes initializing the File IO Controller, Invoice Processor,
        and GUI Display
        """

        # Argument provider to check for integration test mode
        self.argument_provider = ArgumentProvider(
            description="Fishbowl invoice cost-breakdown processor"
        )

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
        self.settings_repository = SettingsRepository(db_path=SETTINGS_DB_PATH)

        # Held onto rather than used and discarded: as well as restoring the
        # display's theme/font below, they carry the version this user last
        # launched, which start_application() compares against VERSION.
        self.saved_settings = self.settings_repository.get_all_settings()

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
            check_for_updates_callback=self.handle_check_for_updates,
            view_patch_notes_callback=self.handle_view_patch_notes,
            settings=self.saved_settings,
        )

        # Wire the GUI's popup into the File IO Controller and Settings Repository
        # so file/database failures surface to the user without coupling those
        # components to the GUI. This must happen before the config files are
        # parsed below so parse failures can be reported.
        self.file_io_controller.report_error = self.display.show_popup
        self.settings_repository.report_error = self.display.show_popup

        # Create the Update Coordinator, which owns the background release check
        # and reports its outcome through the display created above. The asset
        # pattern names this app's installer among the release's assets, which is
        # what lets the user update in place rather than downloading it by hand.
        self.update_coordinator = UpdateCoordinator(
            current_version=VERSION,
            repo=GITHUB_REPO,
            display=self.display,
            asset_pattern=INSTALLER_ASSET_PATTERN,
        )

        # Create the reader over the patch notes packaged next to the executable,
        # which tells the user what changed after an update. Constructing it reads
        # nothing -- the file is read on each call -- so it is built here with the
        # rest of the collaborators and only consulted from the GUI branch of
        # start_application(), the same shape the Update Coordinator above has.
        self.patch_notes = PatchNotes(notes_path=PATCH_NOTES_PATH)

        # Use the File IO Controller to read in the criteria/exclusions for each cost section
        self.file_io_controller.parse_cost_criteria_file()

        # Build payment terms dictionary containing all possible sales rep name codes that could appear on an invoice
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

        # Build sales_rep dictionary containing all possible payment terms that could appear on an invoice
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()

    ###########################################################################
    ###             InvoiceAppController -> start_application()             ###
    ###########################################################################
    def start_application(self) -> None:
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
            self.update_coordinator.start()

            # Tell the user what changed if this is the first launch after an
            # update. Confined to this branch, like the update check above, so an
            # integration-test run reads no notes and opens no window -- this
            # controller builds its display up front, so the gate has to be
            # explicit rather than falling out of where the GUI is created.
            self.show_patch_notes_if_updated(self.saved_settings)

            # Else, normally start the GUI application
            self.display.mainloop()

    ###########################################################################
    ###          InvoiceAppController -> handle_check_for_updates()         ###
    ###########################################################################
    def handle_check_for_updates(self) -> None:
        """
        Runs an on-demand update check, triggered by the Help menu's
        "Check for Updates" item. Wired into the display as its update callback,
        which is the display's only route to the network. Flags the check as
        manual so the user always gets feedback about the outcome.
        """

        self.update_coordinator.start(manual=True)

    ###########################################################################
    ###         InvoiceAppController -> handle_view_patch_notes()           ###
    ###########################################################################
    def handle_view_patch_notes(self) -> None:
        """
        Shows the patch notes on demand, triggered by the Help menu's "What's New"
        item. Every version up to the running one is shown, newest first, since a
        user who has already dismissed an update's notes has no other way back to
        them. Wired into the display as its patch notes callback.
        """

        notes = self.patch_notes.notes_since(VERSION, None)

        # Unlike the silent startup check below, a request the user made
        # explicitly is answered even when there is nothing to show
        if notes:
            self.display.show_patch_notes(APP_NAME, VERSION, notes)
        else:
            self.display.show_popup(
                title="No Patch Notes",
                message=f"No patch notes found at: {PATCH_NOTES_PATH}.",
            )

    ###########################################################################
    ###        InvoiceAppController -> show_patch_notes_if_updated()        ###
    ###########################################################################
    def show_patch_notes_if_updated(self, saved_settings: dict[str, str]) -> None:
        """
        Shows the user what changed when this launch is the first one after an
        update, and records the running version either way.

        Nothing is shown on a fresh install (no version was ever stored), on an
        ordinary relaunch, or after a downgrade: in none of those cases did an
        update just happen. The very first launch after upgrading into this
        feature shows nothing either, since a user coming from a build that never
        wrote the setting is indistinguishable from a first-time user.

        Args:
            saved_settings (dict[str, str]): The settings persisted by the last
                run, holding the version that run was on
        """

        last_seen_version = saved_settings.get(SETTING_KEY_LAST_SEEN_VERSION)

        # Record the running version before deciding anything, so an update's
        # notes are shown once rather than on every launch that follows it
        self.handle_save_setting(SETTING_KEY_LAST_SEEN_VERSION, VERSION)

        if not last_seen_version or compare_versions(last_seen_version, VERSION) >= 0:
            return

        # Every version the user passed through, not just the one they landed on
        notes = self.patch_notes.notes_since(VERSION, last_seen_version)
        if not notes:
            return

        # Open the window once the main loop is running rather than inline: the
        # shared window centers itself over this one, whose geometry reads as
        # 1x1+0+0 until the root window has been mapped, so an inline call would
        # put the notes in the corner of the screen instead of over the app
        self.display.after(0, self.display.show_patch_notes, APP_NAME, VERSION, notes)

    ###########################################################################
    ###          InvoiceAppController -> handle_process_invoice()           ###
    ###########################################################################
    def handle_process_invoice(
        self, invoice_filepath: Path, append_output: bool
    ) -> None:
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
            self.display.show_popup(
                title="Error",
                message=f"No pages were found in the invoice PDF located at {invoice_filepath}.",
            )
            return

        # A PDF whose pages hold no text at all cannot be parsed, and failing here
        # rather than pressing on is the whole point of the check: every field
        # would otherwise fall back to its default and the app would report a
        # confident $0.00 breakdown for an invoice it never actually read. The
        # totals would agree at $0.00, so even the mismatch warning below would
        # stay silent. This is what a PDF re-printed through a virtual printer
        # (e.g. "Microsoft Print to PDF") looks like: the page is stored as an
        # image, or its text as vector outlines, with no text layer left behind.
        if not any(page and page.strip() for page in invoice.page_contents):
            self.display.show_popup(
                title="No Readable Text",
                message=(
                    f"No text could be read from the invoice PDF located at {invoice_filepath}. "
                    "It appears to be a scanned or printed-to-PDF copy, which stores the page "
                    "as an image and leaves no text for the app to read. Save the invoice "
                    "directly from Fishbowl instead of printing it to PDF, then try again."
                ),
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
            self.display.show_popup(
                title="Calculated Total Mismatch",
                message=f"The calculated total of ${invoice.total} does not match the listed total of ${invoice.listed_total} for invoice {invoice.order_number}.",
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
    def handle_save_config(self, config_path: Path, contents: str) -> None:
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
    def handle_save_setting(self, key: str, value: str) -> None:
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
    def _reload_cost_criteria(self) -> None:
        """
        Re-parses the cost criteria config into the File IO Controller's criteria
        lists (cleared and repopulated in place, so the InvoiceProcessor's
        references stay valid).
        """
        self.file_io_controller.parse_cost_criteria_file()

    ###########################################################################
    ###           InvoiceAppController -> _reload_payment_terms()           ###
    ###########################################################################
    def _reload_payment_terms(self) -> None:
        """
        Re-parses the payment terms config into the controller's payment_terms list
        """
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

    ###########################################################################
    ###            InvoiceAppController -> _reload_sales_reps()             ###
    ###########################################################################
    def _reload_sales_reps(self) -> None:
        """
        Re-parses the sales reps config into the controller's sales_reps dictionary
        """
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()
