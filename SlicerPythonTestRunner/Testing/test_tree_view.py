import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from SlicerPythonTestRunnerLib import (
    Outcome,
    Results,
    RunnerLogic,
    RunSettings,
    TreeView,
    runTestInSlicerContext,
)
from Testing.utils import (
    a_file_with_one_passed_one_failed_one_skipped_content,
    write_file,
)


@pytest.fixture
def an_empty_test_result_file(tmpdir):
    f_path = Path(tmpdir).joinpath("empty.json")
    with open(f_path, "w") as f:
        f.write(json.dumps({}))
    return f_path


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_tree_view_can_be_refreshed_with_empty_test_case(an_empty_test_result_file):
    view = TreeView()
    view.appendResults(Results.fromReportFile(an_empty_test_result_file))
    assert view.getCaseCount() == 0


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_tree_view_is_populated_by_test_results(a_json_test_result_file):
    view = TreeView()
    view.appendResults(Results.fromReportFile(a_json_test_result_file))
    assert view.getCaseCount() == 3


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_tree_view_displays_test_result_outcomes(a_json_test_result_file):
    view = TreeView()
    view.appendResults(Results.fromReportFile(a_json_test_result_file))

    exp_outcomes = {
        "test_failing_file.py": Outcome.failed,
        "test_failing_file.py::test_failing": Outcome.failed,
        "test_success_file_two_tests.py": Outcome.passed,
        "test_success_file_two_tests.py::test_success_1": Outcome.passed,
        "test_success_file_two_tests.py::test_success_2": Outcome.passed,
    }
    assert view.getOutcomes() == exp_outcomes


@pytest.fixture()
def a_file_with_one_passed_one_failed_one_skipped(tmpdir):
    return write_file(tmpdir, "test_3_tests.py", a_file_with_one_passed_one_failed_one_skipped_content())


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_tree_view_notifies_clicked_cases(a_json_test_result_file):
    view = TreeView()
    view.appendResults(Results.fromReportFile(a_json_test_result_file))

    callMock = MagicMock()

    view.currentCaseTextChanged.connect(callMock)

    view.onItemClicked(None)
    assert callMock.called
    assert callMock.call_args


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_tree_view_can_filter_passed_and_ignored_tests(a_file_with_one_passed_one_failed_one_skipped, tmpdir):
    import slicer

    results = RunnerLogic().runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert results.executedNumber == 3

    view = TreeView()
    view.appendResults(results)

    view.setShowPassed(True)
    view.setShowIgnored(True)
    slicer.app.processEvents()
    fullCount = view.getDisplayedRowCount()

    view.setShowPassed(False)
    slicer.app.processEvents()
    assert view.getDisplayedRowCount() == fullCount - 1

    view.setShowIgnored(False)
    slicer.app.processEvents()
    assert view.getDisplayedRowCount() == fullCount - 2
