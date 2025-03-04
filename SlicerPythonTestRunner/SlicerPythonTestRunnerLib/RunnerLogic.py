import os
import subprocess
import sys
import tempfile
import traceback
from copy import deepcopy
from pathlib import Path
from typing import Union

import coverage

from .Decorator import isRunningInSlicerGui
from .EnsureRequirements import ensureRequirements
from .Results import Results
from .Settings import RunSettings
from .TestCoverage import _coverage, clean_tmp_coverage, write_cov_report


class RunnerLogic:
    """
    Class responsible for launching a 3D Slicer process with pytest and running the different tests.
    The tests run will share the same 3D Slicer instance and should clear the scene if needed.
    """

    def __init__(self, slicer_path=None):
        self.slicer_path = slicer_path or self.default_path()
        self.tmp_path = tempfile.mkdtemp()
        self.i_test_file = 0

    @staticmethod
    def default_path() -> Path:
        if isRunningInSlicerGui():
            import slicer

            return Path(slicer.app.applicationFilePath())

        return next(file for file in Path(sys.executable).parent.glob("SlicerApp*") if file.is_file()).resolve()

    @staticmethod
    def startQProcess(process, args) -> None:
        process.start(args[0], args[1:])

    @classmethod
    def runInSubProcessAndWaitFinished(cls, args):
        if isRunningInSlicerGui():
            import qt

            process = qt.QProcess()
            cls.startQProcess(process, args)
            process.waitForFinished(-1)
        else:
            subprocess.run(args)

    def runAndWaitFinished(
        self,
        directory: Union[str, Path],
        runSettings: RunSettings,
        doRunInSubProcess: bool = True,
    ) -> Results:
        """
        Run the tests given the input settings, wait for the results and returns the results.

        :param directory: Directory in which PyTest will be executed
        :param runSettings: Test settings
        :param doRunInSubProcess: If True, runs in subprocess, otherwise, runs in current Python instance.
            If running in Python instance, the libraries will be loaded once and not reloaded afterward.
            Please use with caution.
        """
        # Make sure the requirements are available before running the tests.
        ensureRequirements(quiet=True)

        if doRunInSubProcess:
            return self._runSubProcessAndParseResults(*self.prepareRun(directory, runSettings))
        else:
            return self._runInLocalPythonAndParseResults(directory, runSettings)

    @classmethod
    def _runSubProcessAndParseResults(cls, args: list[str], jsonResportPath: Path) -> Results:
        cls.runInSubProcessAndWaitFinished(args)
        return Results.fromReportFile(jsonResportPath)

    def _runInLocalPythonAndParseResults(self, directory, runSettings) -> Results:
        # Override the settings in local mode to not close Slicer nor minimize the main window
        runSettings = deepcopy(runSettings)
        runSettings.doCloseSlicerAfterRun = False
        runSettings.doMinimizeMainWindow = False

        # Configure the test python file and run locally with the input directory / json report file
        _, json_report_path = self._createTestPythonFile(directory, runSettings)
        self.runPytestAndExit(directory, json_report_path, runSettings)

        # Return the results
        return Results.fromReportFile(json_report_path)

    def collectSubProcess(self, directory: Union[str, Path], runSettings: RunSettings) -> Results:
        """
        Runs PyTest test collection. Uses the run processing as separate process to make sure that the pytest.main
        execution doesn't leak into previous / next execution.
        """
        return self._runSubProcessAndParseResults(*self.prepareCollect(directory, runSettings))

    def prepareCollect(self, directory: Union[str, Path], runSettings: RunSettings) -> tuple[list[str], Path]:
        return self.prepareRun(
            directory,
            RunSettings(
                doUseMainWindow=False,
                extraSlicerArgs=runSettings.extraSlicerArgs,
                extraPytestArgs=["--collect-only", *runSettings.extraPytestArgs],
            ),
        )

    def prepareRun(self, directory: Union[str, Path], runSettings: RunSettings) -> tuple[list[str], Path]:
        """
        Prepares process args and path to JSON report path corresponding to test run with the input parameters.
        Is compatible with Python's subprocess run and QProcess.
        """
        file_path, json_report_path = self._createTestPythonFile(directory, runSettings)
        args = [
            self.slicer_path.as_posix(),
            "--python-script",
            file_path.as_posix(),
            *runSettings.extraSlicerArgs,
        ]

        noMainWindowArg = "--no-main-window"
        if not runSettings.doUseMainWindow and noMainWindowArg not in args:
            args += [noMainWindowArg]

        return args, json_report_path

    @classmethod
    def runPyTest(
        cls,
        exec_path: Union[str, Path],
        json_report_path: Union[str, Path],
        pytest_args: list[str],
    ) -> int:
        import pytest
        from pytest_jsonreport.plugin import JSONReport

        exec_path = Path(exec_path).resolve().as_posix()
        json_report_path = Path(json_report_path).resolve().as_posix()
        plugin = JSONReport()
        ret = pytest.main(
            [
                exec_path,
                f"--json-report-file={json_report_path}",
                f"--junitxml={json_report_path.replace('.json', '.xml')}",
                f"--html={json_report_path.replace('.json', '.html')}",
                "--capture=tee-sys",
                "--cache-clear",
                *cls.formatPytestArgs(pytest_args),
            ],
            plugins=[plugin],
        )
        return int(ret)

    @staticmethod
    def formatPytestArgs(pytestArgs: list[str]) -> list[str]:
        from datetime import datetime

        from coverage.sqldata import filename_suffix

        suffix = filename_suffix(True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")

        return [arg.format(filename_suffix=suffix, timestamp=timestamp) for arg in pytestArgs]

    @classmethod
    def runPytestAndExit(
        cls,
        path: Union[str, Path],
        json_report_path: Union[str, Path],
        runSettings: RunSettings,
    ) -> int:
        try:
            import slicer  # noqa

            win = slicer.util.mainWindow()
            if win and runSettings.doMinimizeMainWindow:
                win.showMinimized()
            exit_f = slicer.util.exit
        except (ImportError, AttributeError):
            exit_f = sys.exit

        @_coverage(runSettings)
        def runPyTestWithCoverage():
            try:
                return cls.runPyTest(path, json_report_path, runSettings.extraPytestArgs)
            except Exception as e:  # noqa
                traceback.print_exc()
                return 1

        ret = runPyTestWithCoverage()
        if runSettings.doCloseSlicerAfterRun:
            exit_f(ret)
        return ret

    @staticmethod
    def _libPaths() -> list[str]:
        file_dir = Path(__file__).parent
        lib_dir = file_dir.parent
        return [file_dir.resolve().as_posix(), lib_dir.resolve().as_posix()]

    def _createTestPythonFile(self, path: Union[str, Path], runSettings: RunSettings) -> tuple[Path, Path]:
        """
        Creates a python file which will run the current file's `runPytestAndExit` in a new Slicer launcher instance
        with the passed args.

        :returns: Paths to generate file and report file which will be created after execution.
        """

        file_path, json_report_path, run_settings_path = self.updateTemFilePaths()
        runSettings.toFile(run_settings_path)

        file_content = (
            "import sys\n"
            "import os\n"
            f'os.chdir(r"{path}")\n'
            f"sys.path.extend({self._libPaths()})\n"
            "from SlicerPythonTestRunnerLib import RunnerLogic, RunSettings\n"
            f'runSettings = RunSettings.fromFile(r"{run_settings_path.as_posix()}")\n'
            "RunnerLogic.runPytestAndExit(\n"
            f'    r"{path}", r"{json_report_path.as_posix()}", runSettings\n'
            ")\n"
        )

        with open(file_path, "w") as f:
            f.write(file_content)

        return file_path, json_report_path

    def updateTemFilePaths(self) -> tuple[Path, Path, Path]:
        json_report_path = Path(self.tmp_path).joinpath(f"pytest_file_{self.i_test_file}.json")
        file_path = Path(self.tmp_path).joinpath(f"pytest_file_{self.i_test_file}.py")
        run_settings_path = Path(self.tmp_path).joinpath(f"pytest_run_settings_{self.i_test_file}.json")
        self.i_test_file += 1
        return file_path, json_report_path, run_settings_path

    @staticmethod
    def writeCoverageReport(directory: str, runSettings: RunSettings) -> None:
        if not runSettings.doRunCoverage or not os.path.exists(directory):
            return

        cwd = os.getcwd()

        try:
            os.chdir(directory)
            write_cov_report(runSettings)
            clean_tmp_coverage(directory)
        except coverage.exceptions.CoverageException:
            pass
        finally:
            os.chdir(cwd)
