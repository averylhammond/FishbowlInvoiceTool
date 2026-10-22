# Import necessary classes from modules
import threading
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

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
from source.invoice import Invoice
from source.invoice_app_file_io import InvoiceAppFileIO
from source.invoice_processor import InvoiceProcessor

# Imported for the display attribute's annotation only. A runtime import here
# would load tkinter on a headless run, which start_application() goes out of
# its way to avoid.
if TYPE_CHECKING:
    from source.gui.invoice_app_display import InvoiceAppDisplay

# TODO: See if there is a good logging method to add for debugging


# InvoiceAppController class to drive logic for processing invoice PDFs.
class InvoiceAppController:
    def __init__(self) -> None:
        """
        Initializes the InvoiceAppController object

        Only the headless half is built here: the File IO Controller and the
        Invoice Processor. Everything the GUI needs is built in
        start_application(), so an integration-test run never creates it.
        """

        # Argument provider to check for integration test (headless) mode
        self.argument_provider = ArgumentProvider(description="Fishbowl invoice cost-breakdown processor")

        # Create File IO Controller, which reads its file paths from source.constants
        self.file_io_controller = InvoiceAppFileIO()

        # Create InvoiceProcessor. Its cost criteria arrive in _prepare_run(), once the configs are parsed
        self.invoice_processor = InvoiceProcessor(file_io_controller=self.file_io_controller)

        # The parsed configs, empty until _prepare_run() reads them in
        self.payment_terms: list[str] = []
        self.sales_reps: dict[str, str] = {}

        # How processing reports to the user: a message (title, message) and an
        # invoice's output (invoice, append_output). Silent by default, which is
        # what a headless run keeps: these messages carry order numbers, totals
        # and file paths, and customer data must never reach a CI log. The GUI
        # branch of start_application() points them at the display.
        self.show_message: Callable[..., None] = lambda *_, **__: None
        self.show_output: Callable[..., None] = lambda *_, **__: None

        # The GUI, constructed in start_application() rather than here so that a
        # headless run never builds a window or imports tkinter
        self.display: InvoiceAppDisplay | None = None

        # The persisted settings store, constructed alongside the GUI in
        # start_application() so that a headless run touches no database
        self.settings_repository: SettingsRepository | None = None

        # The update coordinator, constructed alongside the GUI in
        # start_application() since it reports its outcome through the display
        self.update_coordinator: UpdateCoordinator | None = None

        # The patch notes reader, constructed alongside the GUI in
        # start_application() since its notes are only ever shown in a window
        self.patch_notes: PatchNotes | None = None

    def start_application(self) -> None:
        """
        Starts the application by building the GUI and entering the tkinter main
        loop until the user exits

        Note: In integration test mode the GUI is skipped entirely and every invoice
        is processed headless instead.
        """

        # In integration test mode, process all invoices headless without a GUI
        if self.argument_provider.integration_test_mode:
            self.run_integration_test()
            return

        # Imported here, after the check above, rather than at module scope so a
        # headless run never loads tkinter
        from source.gui.invoice_app_display import InvoiceAppDisplay  # noqa: PLC0415

        # Load the settings the user last chose so the GUI starts the way they
        # left it. Built here rather than in __init__ for the same reason the GUI
        # is: integration test mode must touch no database and leave no data
        # directory behind. The settings also carry the version this user last
        # launched, which show_patch_notes_if_updated() compares against VERSION.
        self.settings_repository = SettingsRepository(db_path=SETTINGS_DB_PATH)
        saved_settings = self.settings_repository.get_all_settings()

        # Create the InvoiceAppDisplay GUI, providing it with the callbacks it
        # needs: processing invoices, reading a file's contents for the native
        # editor/viewer windows, saving edited config files, and persisting user
        # settings. The saved settings restore the user's last theme/font choices.
        self.display = InvoiceAppDisplay(
            title="Invoice Processor",
            window_resolution="750x750",
            process_callback=self.handle_process_invoice,
            process_all_callback=self.handle_process_all_invoices,
            read_file_callback=self.file_io_controller.read_text_file,
            save_config_callback=self.handle_save_config,
            save_settings_callback=self.handle_save_setting,
            copy_invoice_callback=self.file_io_controller.copy_invoice_file,
            check_for_updates_callback=self.handle_check_for_updates,
            view_patch_notes_callback=self.handle_view_patch_notes,
            settings=saved_settings,
        )

        # Wire the GUI into everything that reports to the user, without coupling
        # any of it to the GUI. File IO errors and processing output can arise on
        # the processing worker thread, so they go through _on_gui_thread() rather
        # than straight to the display; database errors only arise on the GUI
        # thread and stay direct. This must happen before _prepare_run() so a
        # config parse failure reaches the user.
        self.file_io_controller.report_error = partial(self._on_gui_thread, self.display.show_popup)
        self.settings_repository.report_error = self.display.show_popup
        self.show_message = partial(self._on_gui_thread, self.display.show_popup)
        self.show_output = partial(self._on_gui_thread, self.display.display_invoice_output)

        self._prepare_run()

        # Kick off a background check for a newer release before entering the GUI
        # loop. Built here rather than in __init__ because it reports through the
        # display. The asset pattern names this app's installer among the
        # release's assets, which is what lets the user update in place rather
        # than downloading it by hand.
        self.update_coordinator = UpdateCoordinator(
            current_version=VERSION,
            repo=GITHUB_REPO,
            display=self.display,
            asset_pattern=INSTALLER_ASSET_PATTERN,
        )
        self.update_coordinator.start()

        # Tell the user what changed if this is the first launch after an update.
        # Constructing the reader reads nothing; the file is read on each call.
        self.patch_notes = PatchNotes(notes_path=PATCH_NOTES_PATH)
        self.show_patch_notes_if_updated(saved_settings)

        self.display.mainloop()

    def run_integration_test(self) -> None:
        """
        Runs the application headless (no GUI): every invoice PDF in the Invoices/
        folder is processed into logs/results.txt, which lets a CI workflow check
        the results without any GUI interaction.

        Runs on this thread rather than a worker: with no main loop, nothing would
        ever drain what a worker posts back.
        """

        # Surface file I/O failures to stdout since there is no GUI here
        self.file_io_controller.report_error = lambda title, message: print(f"{title}: {message}")

        self._prepare_run()
        self.process_all_invoices()

    def _prepare_run(self) -> None:
        """
        Resets the log files and reads in the config files. Called once the error
        reporter has been wired, so a failure here reaches the user.
        """

        # Reset text files before processing anything
        if __debug__:
            self.file_io_controller.reset_debug_file()

        self.file_io_controller.reset_results_file()

        # Read in the criteria/exclusions for each cost section and hand them to the processor
        self._reload_cost_criteria()

        # Build payment terms list containing all possible payment terms that could appear on an invoice
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

        # Build sales_rep dictionary containing all possible sales rep name codes that could appear on an invoice
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()

    def handle_check_for_updates(self) -> None:
        """
        Runs an on-demand update check, triggered by the Help menu's
        "Check for Updates" item. Wired into the display as its update callback,
        which is the display's only route to the network. Flags the check as
        manual so the user always gets feedback about the outcome.
        """

        self.update_coordinator.start(manual=True)

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
            saved_settings: The settings persisted by the last run, holding the version
                that run was on
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

    def handle_process_invoice(self, invoice_filepath: Path, append_output: bool) -> None:
        """
        Processes the invoice located at invoice_filepath on a background thread.
        Wired into the display as its process callback.

        Args:
            invoice_filepath: The filepath of the invoice PDF to be processed.
            append_output: Whether to append the Invoice outputs to any existing outputs.
        """

        self._start_processing(partial(self.process_invoice, invoice_filepath, append_output))

    def handle_process_all_invoices(self) -> None:
        """
        Processes every invoice in the Invoices/ folder on a background thread.
        Wired into the display as its process-all callback.
        """

        self._start_processing(self.process_all_invoices)

    def _start_processing(self, work: Callable[[], None]) -> None:
        """
        Locks the GUI's processing controls and spawns a daemon thread to run a
        processing job.

        Running on a background thread keeps the window responsive while PDFs are
        parsed. Daemon, so exiting mid-run does not hang the application waiting
        on it.

        Args:
            work: The processing job to run
        """

        # Locked here, on the GUI thread, so a second click cannot start an
        # overlapping run before the worker gets going
        self.display.set_processing(True)
        threading.Thread(target=self._run_processing, args=(work,), daemon=True).start()

    def _run_processing(self, work: Callable[[], None]) -> None:
        """
        Worker-thread body for a processing job. Everything the job shows the user
        reaches the GUI thread through _on_gui_thread().

        Args:
            work: The processing job to run
        """

        try:
            work()

        # BLE001 is suppressed rather than satisfied: this is the outer boundary
        # of the worker thread. The release build has no console, so an uncaught
        # error here would vanish without a trace; it must reach the user as a
        # popup instead.
        except Exception as e:  # noqa: BLE001
            self.show_message(
                title="Processing Error",
                message=f"An error occurred while processing invoices: {e}",
            )
        finally:
            # Unlocked whatever happened, or a failed run would leave the controls
            # disabled for the rest of the session
            self._on_gui_thread(self.display.set_processing, False)

    def _on_gui_thread(self, func: Callable[..., object], *args: object, **kwargs: object) -> None:
        """
        Runs a display call on the GUI thread, which is the only thread allowed to
        touch tkinter. Called from the GUI thread itself (e.g. at startup), it
        runs inline; from the processing worker, it is handed over through
        display.after().

        Args:
            func: The display method to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        """

        if threading.current_thread() is threading.main_thread():
            func(*args, **kwargs)
        else:
            self.display.after(0, partial(func, *args, **kwargs))

    def process_all_invoices(self) -> None:
        """
        Processes every invoice PDF in the Invoices/ folder, appending each one's
        output to the results.txt file and output box. Shared by the GUI's
        "Process All Invoices" button and the headless integration-test run.
        """

        try:
            # Loop through the invoice PDFs in the invoices directory and process each one
            for file_path in self.file_io_controller.list_invoice_files():
                # Process each invoice, appending output to the results.txt file and output widget
                self.process_invoice(file_path, append_output=True)

        # BLE001 is suppressed rather than satisfied: this is the outer boundary
        # over a directory of arbitrary user-supplied PDFs. A parse failure must
        # reach the user as a popup rather than an unhandled crash, so the catch
        # stays broad here even though every handler beneath this layer is narrow.
        except Exception as e:  # noqa: BLE001
            self.show_message(
                title="Processing Error",
                message=f"An error occurred while processing invoices: {e}",
            )

    def process_invoice(self, invoice_filepath: Path, append_output: bool) -> None:
        """
        Directs components to process the invoice located at invoice_filepath

        Args:
            invoice_filepath: The filepath of the invoice PDF to be processed.
            append_output: Whether to append the Invoice outputs to any existing outputs.
                True: append to existing results.txt and output box
                False: overwrite existing results.txt and output box
        """

        invoice = Invoice()

        # Command the File IO Controller to read in the invoice located at invoice_filepath
        invoice.page_contents = self.file_io_controller.read_invoice_file(invoice_filepath=invoice_filepath)

        # If there are no pages in the invoice, show an error and return early
        if not invoice.page_contents or invoice.page_contents[0] is None:
            self.show_message(
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
            self.show_message(
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
        self.show_output(invoice=invoice, append_output=append_output)

        # Invoices generated by Fishbowl are known to have rounding errors, likely due to
        # floating point precision issues, so we need to account for that and let the user
        # know that the generated total may not match the listed total on the invoice.
        # This is done by displaying an error popup window
        if invoice.total != invoice.listed_total:
            self.show_message(
                title="Calculated Total Mismatch",
                message=(
                    f"The calculated total of ${invoice.total} does not match the listed "
                    f"total of ${invoice.listed_total} for invoice {invoice.order_number}."
                ),
            )

        # Print calculated invoice output to results.txt
        self.file_io_controller.print_invoice_to_output_file(invoice=invoice, append_output=append_output)

        # Print completion notice to debug.txt if in debug mode
        self.file_io_controller.print_to_debug_file(contents=f"Processed all sales for invoice: {invoice_filepath}\n")

    def handle_save_config(self, config_path: Path, contents: str) -> None:
        """
        Persists edited config file contents to disk, then re-parses that config
        so the changes take effect in the running application without a restart.

        Args:
            config_path: The config file being saved
            contents: The new contents to write to the config file
        """

        # Write the edited contents to disk
        self.file_io_controller.write_text_file(file_path=config_path, contents=contents)

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

    def handle_save_setting(self, key: str, value: str) -> None:
        """
        Persists a single user setting so it is restored on the next launch.

        Args:
            key: The setting's identifier (e.g. "theme", "font_family")
            value: The setting's value to store
        """

        self.settings_repository.save_setting(key=key, value=value)

    def _reload_cost_criteria(self) -> None:
        """
        Re-parses the cost criteria config and hands the new criteria to the
        InvoiceProcessor
        """
        self.invoice_processor.set_cost_criteria(self.file_io_controller.parse_cost_criteria_file())

    def _reload_payment_terms(self) -> None:
        """
        Re-parses the payment terms config into the controller's payment_terms list
        """
        self.payment_terms = self.file_io_controller.parse_payment_terms_config()

    def _reload_sales_reps(self) -> None:
        """
        Re-parses the sales reps config into the controller's sales_reps dictionary
        """
        self.sales_reps = self.file_io_controller.parse_sales_reps_config()
