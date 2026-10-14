from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

import pytest

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
from source.invoice_app_controller import InvoiceAppController


@pytest.fixture
def controller():
    """
    Builds an InvoiceAppController with every collaborator it constructs replaced
    by a mock, so the controller is exercised in complete isolation (no real file
    I/O, no tkinter window, no PDF parsing).

    Returns:
        types.SimpleNamespace: Holds the constructed controller (`controller`) and
            the mocked collaborator instances (`arg_provider`, `file_io`,
            `processor`, `display`, `coordinator`, `patch_notes`) plus the patched
            `Invoice` class
            so individual tests can configure return values and assert calls.
    """

    with (
        patch("source.invoice_app_controller.ArgumentProvider") as mock_arg_provider_cls,
        patch("source.invoice_app_controller.InvoiceAppFileIO") as mock_file_io_cls,
        patch("source.invoice_app_controller.InvoiceProcessor") as mock_processor_cls,
        patch("source.invoice_app_controller.InvoiceAppDisplay") as mock_display_cls,
        patch("source.invoice_app_controller.SettingsRepository") as mock_settings_repo_cls,
        patch("source.invoice_app_controller.UpdateCoordinator") as mock_coordinator_cls,
        patch("source.invoice_app_controller.PatchNotes") as mock_patch_notes_cls,
        patch("source.invoice_app_controller.Invoice") as mock_invoice_cls,
    ):
        # Grab the instance each patched class returns when constructed
        mock_arg_provider = mock_arg_provider_cls.return_value
        mock_file_io = mock_file_io_cls.return_value
        mock_processor = mock_processor_cls.return_value
        mock_display = mock_display_cls.return_value
        mock_settings_repo = mock_settings_repo_cls.return_value
        mock_coordinator = mock_coordinator_cls.return_value
        mock_patch_notes = mock_patch_notes_cls.return_value

        # Provide the criteria attributes the controller reads off file_io while
        # wiring up the InvoiceProcessor during construction
        mock_file_io.labor_criteria = ["LABOR"]
        mock_file_io.labor_exclusions = ["NO-LABOR"]
        mock_file_io.shipping_criteria = ["SHIPPING"]

        # Config parsing return values the controller stores during construction
        mock_file_io.parse_payment_terms_config.return_value = ["Net 30"]
        mock_file_io.parse_sales_reps_config.return_value = {"REP1": "Rep Name"}

        # Persisted settings the controller loads and hands to the display
        mock_settings_repo.get_all_settings.return_value = {"theme": "Ocean"}

        # Default to GUI (non integration-test) mode
        mock_arg_provider.integration_test_mode = False

        built_controller = InvoiceAppController()

        yield SimpleNamespace(
            controller=built_controller,
            arg_provider_cls=mock_arg_provider_cls,
            arg_provider=mock_arg_provider,
            file_io_cls=mock_file_io_cls,
            file_io=mock_file_io,
            processor_cls=mock_processor_cls,
            processor=mock_processor,
            display_cls=mock_display_cls,
            display=mock_display,
            settings_repo_cls=mock_settings_repo_cls,
            settings_repo=mock_settings_repo,
            coordinator_cls=mock_coordinator_cls,
            coordinator=mock_coordinator,
            patch_notes_cls=mock_patch_notes_cls,
            patch_notes=mock_patch_notes,
            invoice_cls=mock_invoice_cls,
            invoice=mock_invoice_cls.return_value,
        )


def test_init_constructs_and_wires_collaborators(controller):
    """
    Verifies that __init__ constructs each collaborator and wires the
    InvoiceProcessor and InvoiceAppDisplay with the expected dependencies.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Each collaborator should have been constructed exactly once
    controller.arg_provider_cls.assert_called_once_with(description="Fishbowl invoice cost-breakdown processor")
    controller.file_io_cls.assert_called_once_with()

    # The processor is wired with the file_io controller and the criteria pulled
    # off of it
    controller.processor_cls.assert_called_once_with(
        file_io_controller=controller.file_io,
        labor_criteria=["LABOR"],
        labor_exclusions=["NO-LABOR"],
        shipping_criteria=["SHIPPING"],
    )

    # The display is wired with the controller's process callback, the file IO
    # controller's text-file reader, the controller's config save handler, the
    # controller's settings save handler, the file IO controller's invoice copier,
    # and the persisted settings to restore
    controller.display_cls.assert_called_once_with(
        title="Invoice Processor",
        window_resolution="750x750",
        process_callback=controller.controller.handle_process_invoice,
        process_all_callback=controller.controller.handle_process_all_invoices,
        read_file_callback=controller.file_io.read_text_file,
        save_config_callback=controller.controller.handle_save_config,
        save_settings_callback=controller.controller.handle_save_setting,
        copy_invoice_callback=controller.file_io.copy_invoice_file,
        check_for_updates_callback=controller.controller.handle_check_for_updates,
        view_patch_notes_callback=controller.controller.handle_view_patch_notes,
        settings={"theme": "Ocean"},
    )


def test_init_loads_config_files(controller):
    """
    Verifies that __init__ loads the cost criteria, payment terms, and sales reps
    config files and stores the parsed results on the controller.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Cost criteria are parsed into the file_io controller during construction
    controller.file_io.parse_cost_criteria_file.assert_called_once_with()

    # Payment terms and sales reps are parsed and stored on the controller
    controller.file_io.parse_payment_terms_config.assert_called_once_with()
    controller.file_io.parse_sales_reps_config.assert_called_once_with()
    assert controller.controller.payment_terms == ["Net 30"]
    assert controller.controller.sales_reps == {"REP1": "Rep Name"}


def test_init_wires_error_reporter(controller):
    """
    Verifies that __init__ wires the display's error popup into the file IO
    controller and settings repository as their error reporter, so file/database
    failures surface to the user.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The settings repository reports errors straight through the popup, since
    # it only ever fails on the GUI thread
    assert controller.settings_repo.report_error is controller.display.show_popup

    # The file IO controller can also fail on the processing worker, so its
    # reporter is routed through the GUI-thread helper; on this thread it lands
    # on the popup inline
    controller.file_io.report_error("File Error", "Could not read the file")
    controller.display.show_popup.assert_called_once_with("File Error", "Could not read the file")
    controller.display.after.assert_not_called()


def test_init_builds_the_update_coordinator(controller):
    """
    Verifies that __init__ builds the shared UpdateCoordinator with this
    application's version, repository and installer asset pattern, handing it the
    display it reports its outcome through. The asset pattern is what lets the
    coordinator find this app's installer on a release and offer an in-place
    update; the shared package cannot know it, since each app names its own
    installer differently. Constructing it performs no network I/O; only start()
    does.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.coordinator_cls.assert_called_once_with(
        current_version=VERSION,
        repo=GITHUB_REPO,
        display=controller.display,
        asset_pattern=INSTALLER_ASSET_PATTERN,
    )

    # Building the controller must not start a check on its own
    controller.coordinator.start.assert_not_called()


def test_init_builds_the_patch_notes_reader(controller):
    """
    Verifies that __init__ builds the shared PatchNotes reader over the notes file
    packaged next to the executable. Constructing it reads nothing -- the file is
    read on each call -- so it is built with the rest of the collaborators and only
    consulted from the GUI branch of start_application().

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.patch_notes_cls.assert_called_once_with(notes_path=PATCH_NOTES_PATH)

    # Building the controller must not read the notes on its own
    controller.patch_notes.notes_since.assert_not_called()


def test_init_loads_persisted_settings(controller):
    """
    Verifies that __init__ reads the persisted settings from the settings
    repository so they can be handed to the display for restoration.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The settings repository is constructed with the injected database path and
    # queried for the saved settings
    controller.settings_repo_cls.assert_called_once_with(db_path=SETTINGS_DB_PATH)
    controller.settings_repo.get_all_settings.assert_called_once_with()


def test_start_application_resets_files_and_starts_gui(controller):
    """
    Verifies that start_application resets the log files and enters the GUI main
    loop when not in integration test mode.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.arg_provider.integration_test_mode = False

    with patch.object(controller.controller, "process_all_invoices") as mock_process_all:
        controller.controller.start_application()

    # Log files are reset before the application starts
    controller.file_io.reset_debug_file.assert_called_once_with()
    controller.file_io.reset_results_file.assert_called_once_with()

    # The startup update check is kicked off before entering the GUI loop, silently
    # (no manual flag) so being offline never interrupts a launch
    controller.coordinator.start.assert_called_once_with()

    # The GUI main loop is started, and invoices are not processed directly
    controller.display.mainloop.assert_called_once_with()
    mock_process_all.assert_not_called()


def test_start_application_checks_for_patch_notes(controller):
    """
    Verifies that a normal run checks whether this launch is the first one after
    an update, handing the check the settings loaded during construction, before
    entering the GUI loop.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.arg_provider.integration_test_mode = False

    with patch.object(controller.controller, "show_patch_notes_if_updated") as mock_show_patch_notes:
        controller.controller.start_application()

    mock_show_patch_notes.assert_called_once_with({"theme": "Ocean"})


def test_start_application_integration_test_mode_processes_all(controller):
    """
    Verifies that start_application processes all invoices directly (without the
    GUI loop) when running in integration test mode, and never starts the update
    check so no network I/O occurs in the headless CI run.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.arg_provider.integration_test_mode = True

    with patch.object(controller.controller, "process_all_invoices") as mock_process_all:
        controller.controller.start_application()

    # All invoices are processed directly on this thread rather than a worker,
    # since no main loop runs to drain what a worker would post, and the GUI loop
    # is never entered
    mock_process_all.assert_called_once_with()
    controller.display.set_processing.assert_not_called()
    controller.display.mainloop.assert_not_called()

    # The update check is never started in integration test mode
    controller.coordinator.start.assert_not_called()

    # Nor are the patch notes read or shown: this controller builds its display up
    # front, so the headless gate has to be explicit rather than falling out of
    # where the GUI is created
    controller.patch_notes.notes_since.assert_not_called()
    controller.display.after.assert_not_called()


def test_handle_check_for_updates_starts_manual_check(controller):
    """
    Verifies that the Help menu's on-demand handler runs the check through the
    shared coordinator and flags it as manual, so the user always gets feedback
    about the outcome.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.controller.handle_check_for_updates()

    controller.coordinator.start.assert_called_once_with(manual=True)


# Stand-in for what the shared reader returns: one version's section, which the
# controller passes through untouched
NOTES = "## 4.1.7\n\n- Added a thing"


def test_show_patch_notes_if_updated_shows_the_notes_after_an_update(controller):
    """
    Verifies that a launch following an update shows the notes for every version
    the user passed through, and stamps the running version so they are shown once
    rather than on every launch after it.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.patch_notes.notes_since.return_value = NOTES

    controller.controller.show_patch_notes_if_updated({SETTING_KEY_LAST_SEEN_VERSION: "4.0.0"})

    # The whole range is requested, not just the version landed on, so a skipped
    # release is still announced
    controller.patch_notes.notes_since.assert_called_once_with(VERSION, "4.0.0")
    controller.settings_repo.save_setting.assert_called_once_with(key=SETTING_KEY_LAST_SEEN_VERSION, value=VERSION)

    # Opened through after() rather than inline: the shared window centers itself
    # over the main window, whose geometry is not known until it has been mapped
    controller.display.after.assert_called_once_with(
        0,
        controller.display.show_patch_notes,
        APP_NAME,
        VERSION,
        NOTES,
    )


def test_show_patch_notes_if_updated_shows_nothing_on_a_fresh_install(controller):
    """
    Verifies that a launch with no stored version shows nothing but still stamps
    the running version. No update happened: this is either a first-time user, who
    has no interest in what changed before they arrived, or someone upgrading from
    a build that never wrote the setting, which is indistinguishable from one.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.controller.show_patch_notes_if_updated({})

    controller.settings_repo.save_setting.assert_called_once_with(key=SETTING_KEY_LAST_SEEN_VERSION, value=VERSION)
    controller.patch_notes.notes_since.assert_not_called()
    controller.display.after.assert_not_called()


def test_show_patch_notes_if_updated_shows_nothing_on_an_ordinary_relaunch(controller):
    """
    Verifies that reopening the same version shows nothing, so an update's notes
    appear once rather than every time the application starts.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.controller.show_patch_notes_if_updated({SETTING_KEY_LAST_SEEN_VERSION: VERSION})

    controller.patch_notes.notes_since.assert_not_called()
    controller.display.after.assert_not_called()


def test_show_patch_notes_if_updated_shows_nothing_after_a_downgrade(controller):
    """
    Verifies that a launch following a downgrade or a sideways install shows
    nothing and stamps the running version, since the user has already seen these
    notes.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.controller.show_patch_notes_if_updated({SETTING_KEY_LAST_SEEN_VERSION: "99.0.0"})

    controller.settings_repo.save_setting.assert_called_once_with(key=SETTING_KEY_LAST_SEEN_VERSION, value=VERSION)
    controller.patch_notes.notes_since.assert_not_called()
    controller.display.after.assert_not_called()


def test_show_patch_notes_if_updated_shows_nothing_when_there_are_no_notes(controller):
    """
    Verifies that an update whose notes file is missing or says nothing about the
    versions passed through opens no window. The notes are a convenience, so a
    missing file leaves the launch exactly as it was before the feature existed.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.patch_notes.notes_since.return_value = ""

    controller.controller.show_patch_notes_if_updated({SETTING_KEY_LAST_SEEN_VERSION: "4.0.0"})

    controller.display.after.assert_not_called()


def test_handle_view_patch_notes_shows_every_version_up_to_this_one(controller):
    """
    Verifies that the Help menu's "What's New" shows the notes for every version
    up to the running one, so a user who dismissed the window after an update
    still has a way back to what changed.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.patch_notes.notes_since.return_value = NOTES

    controller.controller.handle_view_patch_notes()

    # No lower bound, so every section up to the running version is shown
    controller.patch_notes.notes_since.assert_called_once_with(VERSION, None)
    controller.display.show_patch_notes.assert_called_once_with(APP_NAME, VERSION, NOTES)


def test_handle_view_patch_notes_reports_when_there_are_no_notes(controller):
    """
    Verifies that a request the user made explicitly is answered even when the
    notes file is missing, unlike the silent startup check which simply shows
    nothing.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.patch_notes.notes_since.return_value = ""

    controller.controller.handle_view_patch_notes()

    controller.display.show_patch_notes.assert_not_called()
    controller.display.show_popup.assert_called_once_with(
        title="No Patch Notes",
        message=f"No patch notes found at: {PATCH_NOTES_PATH}.",
    )


def test_handle_process_invoice_runs_on_a_worker_thread(controller):
    """
    Verifies that the display's process callback hands the invoice to a
    background thread rather than processing it inline, and that the job it hands
    over processes that invoice with the requested append flag.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    with (
        patch("source.invoice_app_controller.threading.Thread") as mock_thread_cls,
        patch.object(controller.controller, "process_invoice") as mock_process_invoice,
    ):
        controller.controller.handle_process_invoice(invoice_filepath=Path("invoice.pdf"), append_output=False)

        mock_process_invoice.assert_not_called()
        mock_thread_cls.return_value.start.assert_called_once_with()

        # Run the job the thread was handed, as the worker would
        mock_thread_cls.call_args.kwargs["args"][0]()

    mock_process_invoice.assert_called_once_with(Path("invoice.pdf"), False)


def test_handle_process_all_invoices_runs_on_a_worker_thread(controller):
    """
    Verifies that the display's process-all callback hands the same loop the
    headless run uses to a background thread rather than running it inline.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    with (
        patch("source.invoice_app_controller.threading.Thread") as mock_thread_cls,
        patch.object(controller.controller, "process_all_invoices") as mock_process_all,
    ):
        controller.controller.handle_process_all_invoices()

        mock_process_all.assert_not_called()
        mock_thread_cls.return_value.start.assert_called_once_with()

        mock_thread_cls.call_args.kwargs["args"][0]()

    mock_process_all.assert_called_once_with()


def test_start_processing_locks_the_controls_before_starting_a_daemon_thread(controller):
    """
    Verifies that the processing controls are locked on the GUI thread before the
    worker starts, so a second click cannot overlap the run, and that the worker
    is a daemon so exiting mid-run does not hang the application.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    order = MagicMock()
    work = MagicMock()

    with patch("source.invoice_app_controller.threading.Thread") as mock_thread_cls:
        order.attach_mock(controller.display.set_processing, "set_processing")
        order.attach_mock(mock_thread_cls.return_value.start, "start")
        controller.controller._start_processing(work)

    mock_thread_cls.assert_called_once_with(target=controller.controller._run_processing, args=(work,), daemon=True)
    assert [c[0] for c in order.mock_calls] == ["set_processing", "start"]
    controller.display.set_processing.assert_called_once_with(True)


def test_run_processing_unlocks_the_controls_once_the_job_finishes(controller):
    """
    Verifies that the processing controls are unlocked once the job has finished,
    and only then, with no error shown.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    order = MagicMock()
    work = MagicMock()
    order.attach_mock(work, "work")
    order.attach_mock(controller.display.set_processing, "set_processing")

    controller.controller._run_processing(work)

    assert order.mock_calls == [call.work(), call.set_processing(False)]
    controller.display.show_popup.assert_not_called()


def test_run_processing_reports_and_unlocks_the_controls_on_error(controller):
    """
    Verifies that a job raising an unexpected error still unlocks the processing
    controls, and tells the user rather than failing silently in the
    console-less release build.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.controller._run_processing(MagicMock(side_effect=ValueError("bad page")))

    controller.display.show_popup.assert_called_once()
    assert "bad page" in controller.display.show_popup.call_args.kwargs["message"]
    controller.display.set_processing.assert_called_once_with(False)


def test_on_gui_thread_runs_inline_on_the_gui_thread(controller):
    """
    Verifies that a display call made from the GUI thread itself (startup, the
    headless run) runs immediately rather than waiting on a main loop that may
    never run.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    func = MagicMock()

    controller.controller._on_gui_thread(func, "a", key="b")

    func.assert_called_once_with("a", key="b")
    controller.display.after.assert_not_called()


def test_on_gui_thread_posts_through_after_from_a_worker(controller):
    """
    Verifies that a display call made from the processing worker is handed to the
    GUI thread through after() rather than touching tkinter from the worker, and
    that what it posts makes the original call, keyword arguments included.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    func = MagicMock()

    with patch("source.invoice_app_controller.threading.current_thread", return_value=MagicMock()):
        controller.controller._on_gui_thread(func, "a", key="b")

    func.assert_not_called()
    controller.display.after.assert_called_once()
    delay, posted = controller.display.after.call_args.args
    assert delay == 0

    posted()

    func.assert_called_once_with("a", key="b")


@patch("source.invoice_app_controller.INVOICES_DIR")
def test_process_all_invoices_processes_each(mock_invoices_dir, controller):
    """
    Verifies that process_all_invoices iterates the invoices directory and
    processes each file in order with append_output True.

    Args:
        mock_invoices_dir (unittest.mock.MagicMock): Mocks the INVOICES_DIR constant
        controller (pytest.fixture): Provides the controller and its mocks
    """

    first_invoice = MagicMock()
    second_invoice = MagicMock()
    mock_invoices_dir.resolve.return_value.iterdir.return_value = [first_invoice, second_invoice]

    with patch.object(controller.controller, "process_invoice") as mock_process_invoice:
        controller.controller.process_all_invoices()

    assert mock_process_invoice.call_args_list == [
        call(first_invoice, append_output=True),
        call(second_invoice, append_output=True),
    ]


@patch("source.invoice_app_controller.INVOICES_DIR")
def test_process_all_invoices_error_shows_popup(mock_invoices_dir, controller):
    """
    Verifies that process_all_invoices shows an error popup when iterating the
    invoices directory raises an exception.

    Args:
        mock_invoices_dir (unittest.mock.MagicMock): Mocks the INVOICES_DIR constant
        controller (pytest.fixture): Provides the controller and its mocks
    """

    mock_invoices_dir.resolve.return_value.iterdir.side_effect = OSError("directory unavailable")

    controller.controller.process_all_invoices()

    controller.display.show_popup.assert_called_once()


def test_process_invoice_no_pages_shows_error_and_returns(controller):
    """
    Verifies that process_invoice shows an error popup and returns early
    when the invoice PDF has no pages.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The PDF read returns no pages
    controller.file_io.read_invoice_file.return_value = []

    controller.controller.process_invoice(invoice_filepath="missing.pdf", append_output=False)

    # An error popup is shown and processing stops before populating the invoice
    controller.display.show_popup.assert_called_once()
    controller.processor.populate_invoice.assert_not_called()
    controller.processor.process_invoice.assert_not_called()


def test_process_invoice_first_page_none_shows_error_and_returns(controller):
    """
    Verifies that process_invoice shows an error popup and returns early
    when the first page of the invoice PDF is None.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The PDF read returns a page list whose first page failed to parse
    controller.file_io.read_invoice_file.return_value = [None]

    controller.controller.process_invoice(invoice_filepath="bad.pdf", append_output=False)

    # An error popup is shown and processing stops before populating the invoice
    controller.display.show_popup.assert_called_once()
    controller.processor.populate_invoice.assert_not_called()


def test_process_invoice_no_text_shows_error_and_returns(controller):
    """
    Verifies that process_invoice shows an error popup and returns early
    when the invoice PDF has pages but none of them hold any text, as happens
    with a scanned or printed-to-PDF copy that carries no text layer.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The PDF read returns pages, but every one of them extracted as blank
    controller.file_io.read_invoice_file.return_value = ["", "   \n", ""]

    controller.controller.process_invoice(invoice_filepath="scanned.pdf", append_output=False)

    # An error popup is shown and processing stops before populating the invoice,
    # so no all-zero result is displayed or written to the results file
    controller.display.show_popup.assert_called_once()
    controller.processor.populate_invoice.assert_not_called()
    controller.processor.process_invoice.assert_not_called()
    controller.display.display_invoice_output.assert_not_called()
    controller.file_io.print_invoice_to_output_file.assert_not_called()


def test_process_invoice_text_on_later_page_is_processed(controller):
    """
    Verifies that process_invoice processes an invoice whose first page
    extracted as blank but which holds text on a later page, so the no-text guard
    rejects only PDFs that are blank throughout.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # The first page came back blank, but a later page carries the table
    controller.file_io.read_invoice_file.return_value = ["", "page two text"]
    controller.invoice.total = Decimal("10.00")
    controller.invoice.listed_total = Decimal("10.00")

    controller.controller.process_invoice(invoice_filepath="invoice.pdf", append_output=False)

    # The invoice is processed as normal, with no popup shown
    controller.processor.process_invoice.assert_called_once_with(invoice=controller.invoice)
    controller.display.show_popup.assert_not_called()


def test_process_invoice_full_flow_totals_match(controller):
    """
    Verifies the full happy-path flow: when the calculated total matches the
    listed total, the invoice is populated, processed, displayed, and written to
    the output file with no mismatch popup.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # A single valid page is read, and the totals match
    controller.file_io.read_invoice_file.return_value = ["page one text"]
    controller.invoice.total = Decimal("10.00")
    controller.invoice.listed_total = Decimal("10.00")

    controller.controller.process_invoice(invoice_filepath="invoice.pdf", append_output=True)

    # The processor is asked to populate and process the invoice
    controller.processor.populate_invoice.assert_called_once_with(
        invoice=controller.invoice,
        sales_reps=controller.controller.sales_reps,
        payment_terms=controller.controller.payment_terms,
    )
    controller.processor.process_invoice.assert_called_once_with(invoice=controller.invoice)

    # The output is displayed and written, honoring the append_output flag
    controller.display.display_invoice_output.assert_called_once_with(invoice=controller.invoice, append_output=True)
    controller.file_io.print_invoice_to_output_file.assert_called_once_with(
        invoice=controller.invoice, append_output=True
    )

    # No mismatch popup is shown when the totals match
    controller.display.show_popup.assert_not_called()


def test_process_invoice_total_mismatch_shows_popup(controller):
    """
    Verifies that process_invoice shows a mismatch error popup when the
    calculated total does not match the listed total, while still writing output.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # A single valid page is read, but the totals disagree
    controller.file_io.read_invoice_file.return_value = ["page one text"]
    controller.invoice.total = Decimal("10.00")
    controller.invoice.listed_total = Decimal("9.99")

    controller.controller.process_invoice(invoice_filepath="invoice.pdf", append_output=False)

    # A mismatch popup is shown, and the output is still written
    controller.display.show_popup.assert_called_once()
    controller.file_io.print_invoice_to_output_file.assert_called_once_with(
        invoice=controller.invoice, append_output=False
    )


def test_handle_save_config_cost_criteria_writes_and_reparses(controller):
    """
    Verifies that saving the cost criteria config writes the contents to disk and
    re-parses the cost criteria into the file IO controller.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Ignore the parse call made during construction so the reload can be asserted
    controller.file_io.parse_cost_criteria_file.reset_mock()

    controller.controller.handle_save_config(COST_CRITERIA_PATH, "new criteria")

    # The contents are written, then the cost criteria are reloaded
    controller.file_io.write_text_file.assert_called_once_with(file_path=COST_CRITERIA_PATH, contents="new criteria")
    controller.file_io.parse_cost_criteria_file.assert_called_once_with()


def test_handle_save_config_payment_terms_writes_and_reloads(controller):
    """
    Verifies that saving the payment terms config writes the contents to disk and
    reloads the controller's payment_terms from the re-parsed config.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Ignore the parse call made during construction and supply a new parse result
    controller.file_io.parse_payment_terms_config.reset_mock()
    controller.file_io.parse_payment_terms_config.return_value = ["Net 60"]

    controller.controller.handle_save_config(PAYMENT_TERMS_PATH, "Net 60")

    # The contents are written and the reloaded terms are stored on the controller
    controller.file_io.write_text_file.assert_called_once_with(file_path=PAYMENT_TERMS_PATH, contents="Net 60")
    controller.file_io.parse_payment_terms_config.assert_called_once_with()
    assert controller.controller.payment_terms == ["Net 60"]


def test_handle_save_config_sales_reps_writes_and_reloads(controller):
    """
    Verifies that saving the sales reps config writes the contents to disk and
    reloads the controller's sales_reps from the re-parsed config.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Ignore the parse call made during construction and supply a new parse result
    controller.file_io.parse_sales_reps_config.reset_mock()
    controller.file_io.parse_sales_reps_config.return_value = {"REP2": "New Rep"}

    controller.controller.handle_save_config(SALES_REPS_PATH, "REP2=New Rep")

    # The contents are written and the reloaded reps are stored on the controller
    controller.file_io.write_text_file.assert_called_once_with(file_path=SALES_REPS_PATH, contents="REP2=New Rep")
    controller.file_io.parse_sales_reps_config.assert_called_once_with()
    assert controller.controller.sales_reps == {"REP2": "New Rep"}


def test_handle_save_config_unknown_path_writes_without_reparsing(controller):
    """
    Verifies that saving an unmanaged file path writes the contents but triggers
    no config re-parse.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    # Ignore the parse calls made during construction
    controller.file_io.parse_cost_criteria_file.reset_mock()
    controller.file_io.parse_payment_terms_config.reset_mock()
    controller.file_io.parse_sales_reps_config.reset_mock()

    controller.controller.handle_save_config(Path("logs/results.txt"), "data")

    # The file is written, but no config is reloaded
    controller.file_io.write_text_file.assert_called_once_with(file_path=Path("logs/results.txt"), contents="data")
    controller.file_io.parse_cost_criteria_file.assert_not_called()
    controller.file_io.parse_payment_terms_config.assert_not_called()
    controller.file_io.parse_sales_reps_config.assert_not_called()


def test_handle_save_setting_delegates_to_repository(controller):
    """
    Verifies that handle_save_setting forwards the key/value to the settings
    repository to be persisted.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.controller.handle_save_setting("theme", "Forest")

    # The setting is persisted through the settings repository
    controller.settings_repo.save_setting.assert_called_once_with(key="theme", value="Forest")
