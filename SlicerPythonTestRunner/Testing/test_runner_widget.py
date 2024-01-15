from pathlib import Path

import pytest

from SlicerPythonTestRunnerLib import runTestInSlicerContext, RunnerWidget, RunSettings, SettingsDialog
import slicer


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_be_created_and_displayed():
    widget = RunnerWidget()
    widget.show()
    slicer.app.processEvents()


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_display_test_results_and_clicked_cases(a_json_test_result_file):
    widget = RunnerWidget()
    widget.loadResults(a_json_test_result_file)
    assert widget.treeView.getCaseCount()
    widget.treeView.onItemClicked(None)
    assert widget.testResultTextEdit.toPlainText()


@pytest.fixture
def a_folder_with_tests(tmpdir):
    with open(Path(tmpdir).joinpath("test_file.py"), "w") as f:
        f.write(
            "def test_pass():\n"
            "  pass\n"
            "def test_fail():\n"
            "  assert False\n"
        )
    return tmpdir


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_runner_widget_can_collect_tests(a_folder_with_tests):
    widget = RunnerWidget()
    widget.dirPathLineEdit.currentPath = a_folder_with_tests

    widget.collectButton.clicked()
    widget.runProcess.waitForFinished()
    assert widget.treeView.getCaseCount() == 2

    widget.runButton.clicked()
    widget.runProcess.waitForFinished()
    assert widget.treeView.getCaseCount() == 2


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_settings_dialog_can_be_opened():
    d = SettingsDialog(RunSettings())
    d.show()
    d.okButton.clicked()
    d.cancelButton.clicked()
    assert d.getRunSettings()
