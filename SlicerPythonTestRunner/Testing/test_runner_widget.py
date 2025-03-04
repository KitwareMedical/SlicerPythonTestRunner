from pathlib import Path

import pytest
import slicer
from SlicerPythonTestRunnerLib import (
    ModuleSettings,
    RunnerWidget,
    RunSettings,
    SettingsDialog,
    runTestInSlicerContext,
)
from SlicerPythonTestRunnerLib.ExportDialog import ExportDialog
from SlicerPythonTestRunnerLib.ProcessRunnerLogic import ProcessRunnerLogic
from Testing.utils import (
    a_succeeding_test_file_with_two_tests_content,
    a_test_file_with_passing_failing_tests_content,
    write_file,
)


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_be_created_and_displayed():
    widget = RunnerWidget()
    slicer.app.aboutToQuit.connect(widget.close)
    widget.show()
    slicer.app.processEvents()


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_display_test_results_and_clicked_cases(a_json_test_result_file, tmpdir):
    widget = RunnerWidget()
    widget.onResultsAvailable(a_json_test_result_file)
    assert widget.treeView.getCaseCount()
    widget.treeView.onItemClicked(None)
    assert widget.testResultTextEdit.toPlainText()


@pytest.fixture
def a_folder_with_tests(tmpdir):
    write_file(tmpdir, "test_file.py", a_test_file_with_passing_failing_tests_content())
    return tmpdir


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_collect_tests(a_folder_with_tests):
    widget = RunnerWidget()
    widget.dirPathLineEdit.currentPath = a_folder_with_tests

    widget.collectButton.clicked()
    widget.waitForFinished()
    assert widget.treeView.getCaseCount() == 2

    widget.runButton.clicked()
    widget.waitForFinished()
    assert widget.treeView.getCaseCount() == 2


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_settings_dialog_can_be_opened():
    d = SettingsDialog(RunSettings())
    slicer.app.aboutToQuit.connect(d.close)
    d.show()
    d.okButton.clicked()
    d.cancelButton.clicked()
    assert d.getRunSettings()


@pytest.fixture()
def a_folder_with_two_test_files(tmpdir):
    write_file(tmpdir, "test_file.py", a_test_file_with_passing_failing_tests_content())
    write_file(tmpdir, "test_file_2.py", a_succeeding_test_file_with_two_tests_content())
    return tmpdir


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_run_tests_in_parallel(
    a_folder_with_two_test_files,
):
    widget = RunnerWidget()
    widget.dirPathLineEdit.currentPath = a_folder_with_two_test_files
    widget.parallelRunButton.clicked()
    widget.waitForFinished()
    assert widget.treeView.getCaseCount() == 4


@runTestInSlicerContext(
    RunSettings(
        doUseMainWindow=False,
        doMinimizeMainWindow=False,
        extraSlicerArgs=["--disable-modules"],
    )
)
def test_a_runner_can_cancel_tests_in_parallel(a_folder_with_two_test_files):
    widget = RunnerWidget()
    widget.dirPathLineEdit.currentPath = a_folder_with_two_test_files

    widget.parallelRunButton.clicked()
    widget.stopButton.clicked()
    widget.waitForFinished()


@runTestInSlicerContext(
    RunSettings(
        doUseMainWindow=False,
        doMinimizeMainWindow=False,
        extraSlicerArgs=["--disable-modules"],
    )
)
def test_runner_parallel_results_can_be_combined(a_folder_with_two_test_files, tmpdir):
    widget = RunnerWidget()
    widget.dirPathLineEdit.currentPath = a_folder_with_two_test_files

    widget.parallelRunButton.clicked()
    widget.waitForFinished()

    # Test export to HTML and XML using export dialog
    exportXml = Path(tmpdir) / "subfolder/sub/export.xml"
    exportHtml = Path(tmpdir) / "export.html"

    xmlPath, htmlPath = widget.combineReportFiles(tmpdir)
    assert xmlPath.is_file()
    assert htmlPath.is_file()

    dialog = ExportDialog(xmlPath, htmlPath, Path(tmpdir))
    dialog.exportPath.text = exportXml.as_posix()
    dialog.onAccept()

    dialog.exportPath.text = exportHtml.as_posix()
    dialog.onAccept()

    assert exportHtml.is_file()
    assert exportXml.is_file()

    dialog.show()


@runTestInSlicerContext(
    RunSettings(
        doUseMainWindow=False,
        doMinimizeMainWindow=False,
        extraSlicerArgs=["--disable-modules"],
    )
)
def test_runner_doesnt_hang_on_empty_parallel_run(tmpdir):
    runSettings = ModuleSettings().lastRunSettings
    runSettings.doRunTestFilesIndependently = True

    logic = ProcessRunnerLogic()
    logic.startTest(
        testDir=Path(tmpdir), functionPattern="", filePattern="", runSettings=runSettings, doCollectOnly=False
    )
    logic.waitForFinished()
