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
from source.cost_criteria import CostCriteria
from source.invoice_app_controller import InvoiceAppController


@pytest.fixture
def unstarted_controller():
    """
    Builds an InvoiceAppController with every collaborator it constructs replaced
    by a mock, so the controller is exercised in complete isolation (no real file
    I/O, no tkinter window, no database, no PDF parsing). The controller is left
    as __init__ leaves it, before start_application() has built the GUI half.

    The display is patched at its definition site rather than on the controller's
    module: the controller imports it inside start_application(), so the name never
    exists at module scope there.

    Returns:
        types.SimpleNamespace: Holds the constructed controller (`controller`), the
            mocked collaborator classes (`..._cls`) and the instances they return
            (`arg_provider`, `file_io`, `processor`, `display`, `settings_repo`,
            `coordinator`, `patch_notes`), plus the patched `Invoice` class, so
            individual tests can configure return values and assert calls.
    """

    with (
        patch("source.invoice_app_controller.ArgumentProvider") as mock_arg_provider_cls,
        patch("source.invoice_app_controller.InvoiceAppFileIO") as mock_file_io_cls,
        patch("source.invoice_app_controller.InvoiceProcessor") as mock_processor_cls,
        patch("source.gui.invoice_app_display.InvoiceAppDisplay") as mock_display_cls,
        patch("source.invoice_app_controller.SettingsRepository") as mock_settings_repo_cls,
        patch("source.invoice_app_controller.UpdateCoordinator") as mock_coordinator_cls,
        patch("source.invoice_app_controller.PatchNotes") as mock_patch_notes_cls,
        patch("source.invoice_app_controller.Invoice") as mock_invoice_cls,
    ):
        # Grab the instance each patched class returns when constructed
        mock_arg_provider = mock_arg_provider_cls.return_value
        mock_file_io = mock_file_io_cls.return_value
        mock_settings_repo = mock_settings_repo_cls.return_value

        # Config parsing return values the controller stores, or hands to the
        # processor, once a run is prepared
        mock_file_io.parse_cost_criteria_file.return_value = CostCriteria(labor=("LABOR",))
        mock_file_io.parse_payment_terms_config.return_value = ["Net 30"]
        mock_file_io.parse_sales_reps_config.return_value = {"REP1": "Rep Name"}

        # No invoices to process unless a test says otherwise
        mock_file_io.list_invoice_files.return_value = []

        # Persisted settings the controller loads and hands to the display
        mock_settings_repo.get_all_settings.return_value = {"theme": "Ocean"}

        # Default to GUI (non integration-test) mode
        mock_arg_provider.integration_test_mode = False

        yield SimpleNamespace(
            controller=InvoiceAppController(),
            arg_provider_cls=mock_arg_provider_cls,
            arg_provider=mock_arg_provider,
            file_io_cls=mock_file_io_cls,
            file_io=mock_file_io,
            processor_cls=mock_processor_cls,
            processor=mock_processor_cls.return_value,
            display_cls=mock_display_cls,
            display=mock_display_cls.return_value,
            settings_repo_cls=mock_settings_repo_cls,
            settings_repo=mock_settings_repo,
            coordinator_cls=mock_coordinator_cls,
            coordinator=mock_coordinator_cls.return_value,
            patch_notes_cls=mock_patch_notes_cls,
            patch_notes=mock_patch_notes_cls.return_value,
            invoice_cls=mock_invoice_cls,
            invoice=mock_invoice_cls.return_value,
        )


@pytest.fixture
def controller(unstarted_controller):
    """
    Builds an InvoiceAppController that has been through a normal, GUI-mode
    start_application(), so its display, settings repository, update coordinator
    and patch notes reader exist and are wired exactly as the real startup wires
    them. The calls startup made are then cleared, so each test asserts only on
    what it triggers itself.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks

    Returns:
        types.SimpleNamespace: The same namespace unstarted_controller provides
    """

    unstarted_controller.controller.start_application()

    for mock in (
        unstarted_controller.file_io,
        unstarted_controller.processor,
        unstarted_controller.display,
        unstarted_controller.settings_repo,
        unstarted_controller.coordinator,
        unstarted_controller.patch_notes,
    ):
        mock.reset_mock()

    return unstarted_controller


def test_init_constructs_the_headless_collaborators(unstarted_controller):
    """
    Verifies that __init__ constructs the argument provider and file IO
    controller, and wires the InvoiceProcessor with the file IO controller only.
    Its cost criteria arrive later, from _prepare_run().

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.arg_provider_cls.assert_called_once_with(
        description="Fishbowl invoice cost-breakdown processor"
    )
    unstarted_controller.file_io_cls.assert_called_once_with()
    unstarted_controller.processor_cls.assert_called_once_with(file_io_controller=unstarted_controller.file_io)
    unstarted_controller.processor.set_cost_criteria.assert_not_called()


def test_init_builds_none_of_the_gui_half(unstarted_controller):
    """
    Verifies that __init__ builds nothing a headless run must avoid: no window,
    no settings database, no update coordinator and no patch notes reader. All of
    them are built in start_application()'s GUI branch instead.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.display_cls.assert_not_called()
    unstarted_controller.settings_repo_cls.assert_not_called()
    unstarted_controller.coordinator_cls.assert_not_called()
    unstarted_controller.patch_notes_cls.assert_not_called()

    assert unstarted_controller.controller.display is None
    assert unstarted_controller.controller.settings_repository is None
    assert unstarted_controller.controller.update_coordinator is None
    assert unstarted_controller.controller.patch_notes is None


def test_init_reads_no_files(unstarted_controller):
    """
    Verifies that __init__ neither resets the log files nor parses the configs.
    Both wait for _prepare_run(), which runs only once an error reporter has been
    wired, so a failure there reaches the user.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.file_io.reset_results_file.assert_not_called()
    unstarted_controller.file_io.parse_cost_criteria_file.assert_not_called()
    unstarted_controller.file_io.parse_payment_terms_config.assert_not_called()
    unstarted_controller.file_io.parse_sales_reps_config.assert_not_called()
    assert unstarted_controller.controller.payment_terms == []
    assert unstarted_controller.controller.sales_reps == {}


def test_init_reports_processing_silently_by_default(unstarted_controller):
    """
    Verifies that, until the GUI wires them, the message and output hooks accept
    any call and do nothing. That is what a headless run keeps: those messages
    carry order numbers, totals and file paths, which must never reach a CI log.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.controller.show_message(title="Error", message="details")
    unstarted_controller.controller.show_output(invoice=MagicMock(), append_output=True)


def test_start_application_builds_the_gui_and_runs_the_main_loop(unstarted_controller):
    """
    Verifies that a normal run builds the display with the controller's callbacks
    and the persisted settings to restore, enters the GUI main loop, and does not
    process any invoices on its own.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    with patch.object(unstarted_controller.controller, "process_all_invoices") as mock_process_all:
        unstarted_controller.controller.start_application()

    unstarted_controller.display_cls.assert_called_once_with(
        title="Invoice Processor",
        window_resolution="750x750",
        process_callback=unstarted_controller.controller.handle_process_invoice,
        process_all_callback=unstarted_controller.controller.handle_process_all_invoices,
        read_file_callback=unstarted_controller.file_io.read_text_file,
        save_config_callback=unstarted_controller.controller.handle_save_config,
        save_settings_callback=unstarted_controller.controller.handle_save_setting,
        copy_invoice_callback=unstarted_controller.file_io.copy_invoice_file,
        check_for_updates_callback=unstarted_controller.controller.handle_check_for_updates,
        view_patch_notes_callback=unstarted_controller.controller.handle_view_patch_notes,
        settings={"theme": "Ocean"},
    )
    assert unstarted_controller.controller.display is unstarted_controller.display

    unstarted_controller.display.mainloop.assert_called_once_with()
    mock_process_all.assert_not_called()


def test_start_application_loads_persisted_settings(unstarted_controller):
    """
    Verifies that a normal run opens the settings database at the injected path
    and reads the saved settings, so they can be handed to the display.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.controller.start_application()

    unstarted_controller.settings_repo_cls.assert_called_once_with(db_path=SETTINGS_DB_PATH)
    unstarted_controller.settings_repo.get_all_settings.assert_called_once_with()
    assert unstarted_controller.controller.settings_repository is unstarted_controller.settings_repo


def test_start_application_wires_the_error_reporters(unstarted_controller):
    """
    Verifies that a normal run wires the display's popup into the file IO
    controller and settings repository as their error reporter, so file/database
    failures surface to the user.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.controller.start_application()
    unstarted_controller.display.reset_mock()

    # The settings repository reports errors straight through the popup, since
    # it only ever fails on the GUI thread
    assert unstarted_controller.settings_repo.report_error is unstarted_controller.display.show_popup

    # The file IO controller can also fail on the processing worker, so its
    # reporter is routed through the GUI-thread helper; on this thread it lands
    # on the popup inline
    unstarted_controller.file_io.report_error("File Error", "Could not read the file")
    unstarted_controller.display.show_popup.assert_called_once_with("File Error", "Could not read the file")
    unstarted_controller.display.after.assert_not_called()


def test_start_application_points_the_processing_hooks_at_the_display(unstarted_controller):
    """
    Verifies that a normal run routes processing messages to the display's popup
    and invoice output to its output box, both through the GUI-thread helper.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.controller.start_application()
    invoice = MagicMock()

    unstarted_controller.controller.show_message(title="Error", message="details")
    unstarted_controller.controller.show_output(invoice=invoice, append_output=True)

    unstarted_controller.display.show_popup.assert_called_once_with(title="Error", message="details")
    unstarted_controller.display.display_invoice_output.assert_called_once_with(invoice=invoice, append_output=True)


def test_start_application_prepares_the_run_after_wiring_the_reporter(unstarted_controller):
    """
    Verifies that the log files are reset and the configs parsed only once the
    display's popup is wired as the error reporter, so a config parse failure
    reaches the user rather than the default no-op.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    reporters_at_parse = []
    unstarted_controller.file_io.parse_cost_criteria_file.side_effect = lambda: reporters_at_parse.append(
        unstarted_controller.file_io.report_error
    )

    unstarted_controller.controller.start_application()

    assert reporters_at_parse == [unstarted_controller.file_io.report_error]
    unstarted_controller.display.show_popup.assert_not_called()
    reporters_at_parse[0]("File Error", "Could not parse")
    unstarted_controller.display.show_popup.assert_called_once_with("File Error", "Could not parse")


def test_start_application_builds_and_starts_the_update_coordinator(unstarted_controller):
    """
    Verifies that a normal run builds the shared UpdateCoordinator with this
    application's version, repository and installer asset pattern, handing it the
    display it reports its outcome through, and starts the startup check. The
    asset pattern is what lets the coordinator find this app's installer on a
    release and offer an in-place update; the shared package cannot know it, since
    each app names its own installer differently.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.controller.start_application()

    unstarted_controller.coordinator_cls.assert_called_once_with(
        current_version=VERSION,
        repo=GITHUB_REPO,
        display=unstarted_controller.display,
        asset_pattern=INSTALLER_ASSET_PATTERN,
    )

    # Silently (no manual flag), so being offline never interrupts a launch
    unstarted_controller.coordinator.start.assert_called_once_with()


def test_start_application_checks_for_patch_notes(unstarted_controller):
    """
    Verifies that a normal run builds the shared PatchNotes reader over the notes
    file packaged next to the executable, then checks whether this launch is the
    first one after an update, handing the check the settings it loaded.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    with patch.object(unstarted_controller.controller, "show_patch_notes_if_updated") as mock_show_patch_notes:
        unstarted_controller.controller.start_application()

    unstarted_controller.patch_notes_cls.assert_called_once_with(notes_path=PATCH_NOTES_PATH)
    mock_show_patch_notes.assert_called_once_with({"theme": "Ocean"})


def test_start_application_integration_test_mode_builds_no_gui(unstarted_controller):
    """
    Verifies that integration test mode runs the headless path and builds none of
    the GUI half: no window, no settings database, no update coordinator (so no
    network I/O) and no patch notes reader.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.arg_provider.integration_test_mode = True

    with patch.object(unstarted_controller.controller, "run_integration_test") as mock_run_integration_test:
        unstarted_controller.controller.start_application()

    mock_run_integration_test.assert_called_once_with()
    unstarted_controller.display_cls.assert_not_called()
    unstarted_controller.settings_repo_cls.assert_not_called()
    unstarted_controller.coordinator_cls.assert_not_called()
    unstarted_controller.patch_notes_cls.assert_not_called()


def test_run_integration_test_reports_file_errors_to_stdout(unstarted_controller, capsys):
    """
    Verifies that a headless run reports file I/O failures to stdout, since there
    is no GUI to show them in.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
        capsys (pytest.fixture): Captures what is printed to stdout
    """

    unstarted_controller.controller.run_integration_test()

    unstarted_controller.file_io.report_error("File Error", "Could not read the file")

    assert capsys.readouterr().out == "File Error: Could not read the file\n"


def test_run_integration_test_prepares_then_processes_all_inline(unstarted_controller):
    """
    Verifies that a headless run prepares the run, then processes every invoice
    directly on this thread rather than a worker, since no main loop runs to
    drain what a worker would post.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    order = MagicMock()

    with (
        patch("source.invoice_app_controller.threading.Thread") as mock_thread_cls,
        patch.object(unstarted_controller.controller, "_prepare_run") as mock_prepare_run,
        patch.object(unstarted_controller.controller, "process_all_invoices") as mock_process_all,
    ):
        order.attach_mock(mock_prepare_run, "prepare_run")
        order.attach_mock(mock_process_all, "process_all_invoices")
        unstarted_controller.controller.run_integration_test()

    assert order.mock_calls == [call.prepare_run(), call.process_all_invoices()]
    mock_thread_cls.assert_not_called()


def test_prepare_run_resets_files_and_loads_configs(unstarted_controller):
    """
    Verifies that _prepare_run resets the log files, then loads the cost criteria,
    payment terms and sales reps configs, handing the cost criteria to the
    processor and storing the rest on the controller.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.controller._prepare_run()

    unstarted_controller.file_io.reset_debug_file.assert_called_once_with()
    unstarted_controller.file_io.reset_results_file.assert_called_once_with()
    unstarted_controller.file_io.parse_cost_criteria_file.assert_called_once_with()
    unstarted_controller.processor.set_cost_criteria.assert_called_once_with(CostCriteria(labor=("LABOR",)))
    unstarted_controller.file_io.parse_payment_terms_config.assert_called_once_with()
    unstarted_controller.file_io.parse_sales_reps_config.assert_called_once_with()
    assert unstarted_controller.controller.payment_terms == ["Net 30"]
    assert unstarted_controller.controller.sales_reps == {"REP1": "Rep Name"}


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
    Verifies that a display call made from the GUI thread itself (e.g. at
    startup) runs immediately rather than waiting on a main loop that is not
    running yet.

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


def test_process_all_invoices_processes_each(controller):
    """
    Verifies that process_all_invoices processes each invoice file the file IO
    controller lists, in the order it lists them, with append_output True.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    first_invoice = MagicMock()
    second_invoice = MagicMock()
    controller.file_io.list_invoice_files.return_value = [first_invoice, second_invoice]

    with patch.object(controller.controller, "process_invoice") as mock_process_invoice:
        controller.controller.process_all_invoices()

    controller.file_io.list_invoice_files.assert_called_once_with()
    assert mock_process_invoice.call_args_list == [
        call(first_invoice, append_output=True),
        call(second_invoice, append_output=True),
    ]


def test_process_all_invoices_error_shows_popup(controller):
    """
    Verifies that process_all_invoices shows an error popup when processing an
    invoice raises an unexpected exception.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    controller.file_io.list_invoice_files.return_value = [MagicMock()]

    with patch.object(controller.controller, "process_invoice", side_effect=ValueError("bad page")):
        controller.controller.process_all_invoices()

    controller.display.show_popup.assert_called_once()
    assert "bad page" in controller.display.show_popup.call_args.kwargs["message"]


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


def test_process_invoice_headless_is_silent_but_writes_results(unstarted_controller):
    """
    Verifies that, with no GUI built, process_invoice still writes the invoice to
    the results file but reports a total mismatch to no one, since its message
    carries customer data that must not reach a CI log.

    Args:
        unstarted_controller (pytest.fixture): Provides the controller and its mocks
    """

    unstarted_controller.file_io.read_invoice_file.return_value = ["page one text"]
    unstarted_controller.invoice.total = Decimal("10.00")
    unstarted_controller.invoice.listed_total = Decimal("9.99")

    unstarted_controller.controller.process_invoice(invoice_filepath="invoice.pdf", append_output=True)

    unstarted_controller.file_io.print_invoice_to_output_file.assert_called_once_with(
        invoice=unstarted_controller.invoice, append_output=True
    )
    unstarted_controller.display_cls.assert_not_called()


def test_handle_save_config_cost_criteria_writes_and_reloads(controller):
    """
    Verifies that saving an edited cost criteria config writes it to disk, then
    re-parses it and hands the newly parsed criteria to the processor, so the
    edit takes effect without a restart. Writing must come first, or the re-parse
    would read the old file.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

    edited = CostCriteria(labor=("BAR",))
    controller.file_io.parse_cost_criteria_file.return_value = edited
    order = MagicMock()
    order.attach_mock(controller.file_io.write_text_file, "write_text_file")
    order.attach_mock(controller.file_io.parse_cost_criteria_file, "parse_cost_criteria_file")
    order.attach_mock(controller.processor.set_cost_criteria, "set_cost_criteria")

    controller.controller.handle_save_config(COST_CRITERIA_PATH, "LABOR CRITERIA:\nBAR")

    assert order.mock_calls == [
        call.write_text_file(file_path=COST_CRITERIA_PATH, contents="LABOR CRITERIA:\nBAR"),
        call.parse_cost_criteria_file(),
        call.set_cost_criteria(edited),
    ]


def test_handle_save_config_payment_terms_writes_and_reloads(controller):
    """
    Verifies that saving the payment terms config writes the contents to disk and
    reloads the controller's payment_terms from the re-parsed config.

    Args:
        controller (pytest.fixture): Provides the controller and its mocks
    """

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

    controller.controller.handle_save_config(Path("logs/results.txt"), "data")

    # The file is written, but no config is reloaded
    controller.file_io.write_text_file.assert_called_once_with(file_path=Path("logs/results.txt"), contents="data")
    controller.file_io.parse_cost_criteria_file.assert_not_called()
    controller.processor.set_cost_criteria.assert_not_called()
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
