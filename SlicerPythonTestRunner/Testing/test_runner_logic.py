from SlicerPythonTestRunnerLib import RunnerLogic, Results, Case, runTestInSlicerContext, RunSettings
import pytest
from pathlib import Path
import qt


@pytest.fixture()
def a_test_runner():
    return RunnerLogic()


@pytest.fixture()
def a_succeeding_test_file(tmpdir):
    file_path = Path(tmpdir).joinpath("test_success_file.py")

    with open(file_path, "w") as f:
        f.write(
            "def test_success():\n"
            "  assert True\n"
        )
    return file_path


def test_runner_can_run_tests_in_given_directory(a_test_runner, a_succeeding_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.passedNumber == 1


@pytest.fixture()
def a_slicer_import_test_file(tmpdir):
    file_path = Path(tmpdir).joinpath("test_slicer_file.py")

    with open(file_path, "w") as f:
        f.write(
            "def test_slicer():\n"
            "  import slicer\n"
            "  node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode')\n"
            "  assert node\n"
        )
    return file_path


def test_runner_is_compatible_with_slicer_content(a_test_runner, a_slicer_import_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.passedNumber == 1


@pytest.fixture()
def a_failing_test_file(tmpdir):
    file_path = Path(tmpdir).joinpath("test_failing_file.py")

    with open(file_path, "w") as f:
        f.write(
            "def test_failing():\n"
            "  assert False\n"
        )
    return file_path


def test_runner_can_run_failing_tests(a_test_runner, a_failing_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.failuresNumber == 1


@pytest.fixture()
def a_succeeding_test_file_with_two_tests(tmpdir):
    file_path = Path(tmpdir).joinpath("test_success_file_two_tests.py")

    with open(file_path, "w") as f:
        f.write(
            "def test_success_1():\n"
            "  pass\n"
            "def test_success_2():\n"
            "  pass\n"
        )
    return file_path


@pytest.fixture()
def a_collection_of_3_test_dir(
        a_failing_test_file,
        a_succeeding_test_file_with_two_tests,
        tmpdir
):
    return tmpdir


def test_runner_tests_can_be_parsed(a_json_test_result_file):
    res = Results.fromReportFile(a_json_test_result_file)
    assert res.executedNumber == 3
    assert res.failuresNumber == 1

    assert len(res.getAllCases()) == 3
    assert len(res.getFailingCases()) == 1

    with pytest.raises(AssertionError):
        assert False, res.getFailingCasesString()


@pytest.fixture()
def a_reporting_failing_test_file(tmpdir):
    file_path = Path(tmpdir).joinpath("test_failing_file.py")

    with open(file_path, "w") as f:
        f.write(
            "import logging\n"
            "import sys\n"
            "def test_failing():\n"
            "  print('STD OUT')\n"
            "  print('STD ERR', file=sys.stderr)\n"
            "  logging.exception('LOGGING EXCEPTION')\n"
            "  logging.debug('LOGGING DEBUG')\n"
            "  logging.warn('LOGGING WARN')\n"
            "  assert False\n"
        )
    return file_path


def test_runner_contains_print_reporting(a_test_runner, a_reporting_failing_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert len(res.getFailingCases()) == 1
    case = res.getFailingCases()[0]
    assert "STD ERR" in case.stderr
    assert "STD OUT" in case.stdout
    assert case.logs
    assert "LOGGING EXCEPTION" in case.logs[0]
    assert "LOGGING DEBUG" in case.logs[1]
    assert "LOGGING WARN" in case.logs[2]


@pytest.fixture
def a_unittest_case_file(tmpdir):
    file_path = Path(tmpdir).joinpath("unittest_file.py")

    with open(file_path, "w") as f:
        f.write(
            "import unittest\n"
            "class MyTestCase(unittest.TestCase):\n"
            "  def test_success(self):\n"
            "    self.assertTrue(True)\n"
            "  def test_failing(self):\n"
            "    self.assertTrue(False)\n"
        )
    return file_path


def test_runner_can_run_unittest_test_case_files(a_test_runner, a_unittest_case_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(
        doUseMainWindow=False,
        extraPytestArgs=RunSettings.pytestClassFilterArgs("*TestCase") + RunSettings.pytestFileFilterArgs("*.py")
    ))
    assert res.executedNumber == 2
    assert res.failuresNumber == 1
    assert res.collectedNumber == 0


def test_runner_can_collect_unittest_test_case_files(a_test_runner, a_unittest_case_file, tmpdir):
    res = a_test_runner.collectSubProcess(tmpdir, RunSettings(
        doUseMainWindow=False,
        extraPytestArgs=RunSettings.pytestClassFilterArgs("*TestCase") + RunSettings.pytestFileFilterArgs("*.py")
    ))
    assert res.executedNumber == 0
    assert res.collectedNumber == 2


def test_runner_can_filter_function_names(a_test_runner, a_succeeding_test_file_with_two_tests, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(
        doUseMainWindow=False,
        extraPytestArgs=RunSettings.pytestFunctionFilterArgs("*_2")
    ))
    assert res.executedNumber == 1
    assert res.passedNumber == 1


def test_runner_can_collect_files_only(a_test_runner, a_collection_of_3_test_dir, tmpdir):
    res = a_test_runner.collectSubProcess(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.collectedNumber == 3
    assert len(res.getAllCases()) == 3


@pytest.mark.parametrize(
    "nodeid, exp_parent_id", [
        ("", ""),
        ("test_case.py", ""),
        ("test_case.py::TestCase::test_hello_world", "test_case.py::TestCase"),
        ("test_case.py::test_my_test", "test_case.py"),
        ("test_case.py::test_my_test::parametrized[A::B::C]", "test_case.py::test_my_test"),
    ]
)
def test_a_case_base_ids(nodeid, exp_parent_id):
    assert Case(nodeid=nodeid).getParentID() == exp_parent_id


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_can_be_run_in_slicer_context():
    import slicer
    print(slicer.app)


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_runner_prepare_run_can_be_used_by_q_process(a_test_runner, a_succeeding_test_file, tmpdir):
    process = qt.QProcess()
    args, path = a_test_runner.prepareRun(directory=tmpdir, runSettings=RunSettings(doUseMainWindow=False))
    a_test_runner.startQProcess(process, args)
    process.waitForFinished()
    assert path.exists()
    results = Results.fromReportFile(path)
    assert results.passedNumber == 1
