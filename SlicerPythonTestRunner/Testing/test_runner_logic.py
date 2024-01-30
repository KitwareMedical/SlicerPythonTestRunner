from pathlib import Path

import pytest
import qt

from SlicerPythonTestRunnerLib import RunnerLogic, Results, Case, runTestInSlicerContext, RunSettings
from Testing.utils import a_reporting_failing_test_content, a_success_test_content, a_slicer_test_content, \
    a_failing_test_content, a_succeeding_test_file_with_two_tests_content, a_unittest_case_content, write_file


@pytest.fixture()
def a_test_runner():
    return RunnerLogic()


@pytest.fixture()
def a_succeeding_test_file(tmpdir):
    return write_file(tmpdir, "test_success_file.py", a_success_test_content())


def test_runner_can_run_tests_in_given_directory(a_test_runner, a_succeeding_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.passedNumber == 1


@pytest.fixture()
def a_slicer_import_test_file(tmpdir):
    return write_file(tmpdir, "test_slicer_file.py", a_slicer_test_content())


def test_runner_is_compatible_with_slicer_content(a_test_runner, a_slicer_import_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.passedNumber == 1


@pytest.fixture()
def a_failing_test_file(tmpdir):
    return write_file(tmpdir, "test_failing_file.py", a_failing_test_content())


def test_runner_can_run_failing_tests(a_test_runner, a_failing_test_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False))
    assert res.failuresNumber == 1


@pytest.fixture()
def a_succeeding_test_file_with_two_tests(tmpdir):
    return write_file(tmpdir, "test_success_file_two_tests.py", a_succeeding_test_file_with_two_tests_content())


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


def test_runner_tests_with_collect_errors_can_be_parsed(a_json_test_with_collect_errors_result_file):
    res = Results.fromReportFile(a_json_test_with_collect_errors_result_file)
    assert res.failuresNumber == 2

    assert len(res.getFailingCases()) == 2

    with pytest.raises(AssertionError):
        assert False, res.getFailingCasesString()


def test_runner_results_ignore_init_file_collection(a_json_test_with_collect_errors_result_file):
    res = Results.fromReportFile(a_json_test_with_collect_errors_result_file)
    assert res.collectedNumber == 0


@pytest.fixture()
def a_reporting_failing_test_file(tmpdir):
    file_path = Path(tmpdir).joinpath("test_failing_file.py")

    with open(file_path, "w") as f:
        f.write(a_reporting_failing_test_content())
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
    return write_file(tmpdir, "unittest_file.py", a_unittest_case_content())


def test_runner_can_run_unittest_test_case_files(a_test_runner, a_unittest_case_file, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(
        doUseMainWindow=False,
        extraPytestArgs=RunSettings.pytestFileFilterArgs("*.py")
    ))
    assert res.executedNumber == 2
    assert res.failuresNumber == 1
    assert res.collectedNumber == 0


def test_runner_can_collect_unittest_test_case_files(a_test_runner, a_unittest_case_file, tmpdir):
    res = a_test_runner.collectSubProcess(tmpdir, RunSettings(
        doUseMainWindow=False,
        extraPytestArgs=RunSettings.pytestFileFilterArgs("*.py")
    ))
    assert res.executedNumber == 0
    assert res.collectedNumber == 2


def test_runner_can_filter_function_names(a_test_runner, a_succeeding_test_file_with_two_tests, tmpdir):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(
        doUseMainWindow=False,
        extraPytestArgs=RunSettings.pytestPatternFilterArgs("_2")
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
        ("A/B/test_case.py::test_my_test", "A/B/test_case.py"),
        ("A\\test_case.py::test_my_test", "A\\test_case.py"),
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


@pytest.mark.parametrize(
    "file_path,cov_format",
    [
        ("report.xml", ["xml"]),
        ("report.json", ["json"]),
        ("report.info", ["lcov"]),
        ("report_dir", ["html"]),
    ]
)
def test_runner_supports_coverage_files(
        a_test_runner,
        a_succeeding_test_file_with_two_tests,
        tmpdir,
        file_path,
        cov_format
):
    coverage_path = Path(tmpdir).joinpath(file_path)
    settings = RunSettings(
        doRunCoverage=True,
        doUseMainWindow=False,
        coverageReportFormats=cov_format,
        coverageFilePath=coverage_path.as_posix()
    )
    a_test_runner.runAndWaitFinished(tmpdir, settings)
    assert coverage_path.exists()


@pytest.fixture
def a_project_with_configuration_files(tmpdir):
    s1 = (
        "def f_a():\n"
        "  print('a')\n"
    )
    s2 = (
        "from .s1 import f_a\n"
        "def f_b():\n"
        "  f_a()\n"
        "  print('b')\n"
    )

    s_init = (
        "from .s1 import *\n"
        "from .s2 import *\n"
    )

    test_a = (
        "from src_lib import f_a\n"
        "def test_f_a():\n"
        "  f_a()\n"
    )

    test_b = (
        "from src_lib import f_b\n"
        "def test_f_b():\n"
        "  f_b()\n"
    )

    pytest_ini = (
        "[pytest]\n"
        "minversion = 6.0\n"
        "pythonpath = ./\n"
        "testpaths =\n"
        "    ./weird_test_name\n"
    )

    coverage_file = (
        "[run]\n"
        "branch = True\n\n"
        "[html]\n"
        "directory = coverage_html_report\n"
    )

    write_file(tmpdir, "src_lib/__init__.py", s_init)
    write_file(tmpdir, "src_lib/s1.py", s1)
    write_file(tmpdir, "src_lib/s2.py", s2)
    write_file(tmpdir, "weird_test_name/test_a.py", test_a)
    write_file(tmpdir, "weird_test_name/test_b.py", test_b)
    write_file(tmpdir, "pytest.ini", pytest_ini)
    write_file(tmpdir, ".coveragerc", coverage_file)

    return tmpdir


def test_runner_uses_local_config_files_if_present_in_the_run_dir(
        tmpdir,
        a_project_with_configuration_files,
        a_test_runner
):
    res = a_test_runner.runAndWaitFinished(tmpdir, RunSettings(doUseMainWindow=False, doRunCoverage=True))
    assert res.executedNumber == 2
    assert res.passedNumber == 2
    report_path = Path(tmpdir).joinpath("coverage_html_report")
    assert report_path.exists()
    assert report_path.joinpath("index.html").exists()


@pytest.fixture
def a_test_case_with_two_tests(tmpdir):
    content = (
        "import unittest\n\n"
        "class MyTestCase(unittest.TestCase):\n\n"
        "  def test_1(self):\n"
        "    pass\n\n"
        "  def test_2(self):\n"
        "    pass\n"
    )

    return write_file(tmpdir, "test_testcase_with_two_tests.py", content)


def test_runner_filter_function_can_run_specific_function_from_test_class(
        tmpdir,
        a_test_case_with_two_tests,
        a_test_runner
):
    res = a_test_runner.runAndWaitFinished(
        tmpdir,
        RunSettings(
            doUseMainWindow=False,
            extraPytestArgs=
            RunSettings.pytestFileFilterArgs("*.py") +
            RunSettings.pytestPatternFilterArgs("test_1")
        )
    )

    assert res.executedNumber == 1
    assert res.passedNumber == 1


@pytest.fixture
def a_dir_with_collect_problems(tmpdir):
    s1 = (
        "from .s2 import f_b\n"
        "def f_a():\n"
        "  pass\n"
    )
    s2 = (
        "from .s1 import f_a\n"
        "def f_b():\n"
        "  pass\n"
    )
    t1 = (
        "from pck.s1 import f_a\n"
        "def test_1():\n"
        "  pass\n"
    )

    t2 = (
        "from pck.s2 import f_b\n"
        "def test_2():\n"
        "  pass\n"
    )

    write_file(tmpdir, "pck/__init__.py", "")
    write_file(tmpdir, "pck/s1.py", s1)
    write_file(tmpdir, "pck/s2.py", s2)
    write_file(tmpdir, "tests/__init__.py", "")
    write_file(tmpdir, "tests/test_1.py", t1)
    write_file(tmpdir, "tests/test_2.py", t2)

    return tmpdir


def test_runner_reports_collect_errors(a_dir_with_collect_problems, a_test_runner):
    res = a_test_runner.runAndWaitFinished(a_dir_with_collect_problems, RunSettings(doUseMainWindow=False))
    assert res.failuresNumber == 2
