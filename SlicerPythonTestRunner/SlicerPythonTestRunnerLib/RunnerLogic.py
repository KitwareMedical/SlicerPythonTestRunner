import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Union

from .TestCoverage import _coverage
from .Decoractor import isRunningInSlicerGui
from .Results import Results
from .Settings import RunSettings


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
        return next(
            file for file in Path(sys.executable).joinpath("..", "..").resolve().glob("Slicer*") if file.is_file()
        ).resolve()

    @staticmethod
    def startQProcess(process: "qt.QProcess", args) -> None:
        process.start(args[0], args[1:])

    @classmethod
    def _runInSubProcessAndWaitFinished(cls, args):
        if isRunningInSlicerGui():
            import qt
            process = qt.QProcess()
            cls.startQProcess(process, args)
            process.waitForFinished(-1)
        else:
            subprocess.run(args)

    def runAndWaitFinished(self, directory: Union[str, Path], runSettings: RunSettings) -> Results:
        return self._runSubProcessAndParseResults(
            *self.prepareRun(directory, runSettings)
        )

    @classmethod
    def _runSubProcessAndParseResults(cls, args: List[str], jsonResportPath: Path) -> Results:
        cls._runInSubProcessAndWaitFinished(args)
        return Results.fromReportFile(jsonResportPath)

    def collectSubProcess(self, directory: Union[str, Path], runSettings: RunSettings) -> Results:
        """
        Runs PyTest test collection. Uses the run processing as separate process to make sure that the pytest.main
        execution doesn't leak into previous / next execution.
        """
        return self._runSubProcessAndParseResults(
            *self.prepareCollect(directory, runSettings)
        )

    def prepareCollect(self, directory: Union[str, Path], runSettings) -> Tuple[List[str], Path]:
        return self.prepareRun(directory, RunSettings(
            doUseMainWindow=False,
            extraSlicerArgs=runSettings.extraSlicerArgs,
            extraPytestArgs=["--collect-only", *runSettings.extraPytestArgs]
        ))

    def prepareRun(self, directory: Union[str, Path], runSettings: RunSettings) -> Tuple[List[str], Path]:
        """
        Prepares process args and path to JSON report path corresponding to test run with the input parameters.
        Is compatible with Python's subprocess run and QProcess.
        """
        file_path, json_report_path = self._createTestPythonFile(directory, runSettings)
        args = [
            self.slicer_path.as_posix(),
            "--python-script",
            file_path.as_posix(),
            *runSettings.extraSlicerArgs
        ]

        noMainWindowArg = "--no-main-window"
        if not runSettings.doUseMainWindow and noMainWindowArg not in args:
            args += [noMainWindowArg]

        return args, json_report_path

    @staticmethod
    def runPyTest(exec_path: Union[str, Path], json_report_path: Union[str, Path], pytest_args: List[str]) -> int:
        import pytest
        from pytest_jsonreport.plugin import JSONReport

        exec_path = Path(exec_path).resolve().as_posix()
        json_report_path = Path(json_report_path).resolve().as_posix()
        plugin = JSONReport()
        ret = pytest.main([
            exec_path,
            f"--json-report-file={json_report_path}",
            "--capture=tee-sys",
            "--cache-clear",
            *pytest_args
        ], plugins=[plugin])
        return int(ret)

    @classmethod
    def runPytestAndExit(
            cls,
            path: Union[str, Path],
            json_report_path: Union[str, Path],
            runSettings: RunSettings
    ) -> int:
        try:
            import slicer  # noqa
            win = slicer.util.mainWindow()
            if win and runSettings.doMinimizeMainWindow:
                win.showMinimized()
            exit_f = slicer.app.exit
        except ImportError:
            exit_f = sys.exit

        @_coverage(runSettings)
        def runPyTestWithCoverage():
            return cls.runPyTest(path, json_report_path, runSettings.extraPytestArgs)

        ret = runPyTestWithCoverage()
        if runSettings.doCloseSlicerAfterRun:
            exit_f(ret)
        return ret

    @staticmethod
    def _libPaths() -> List[str]:
        file_dir = Path(__file__).parent
        lib_dir = file_dir.parent
        return [file_dir.resolve().as_posix(), lib_dir.resolve().as_posix()]

    def _createTestPythonFile(self, path: Union[str, Path], runSettings: RunSettings) -> Tuple[Path, Path]:
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
            f'sys.path.extend({self._libPaths()})\n'
            "from SlicerPythonTestRunnerLib import RunnerLogic, RunSettings\n"
            f'runSettings = RunSettings.fromFile(r"{run_settings_path.as_posix()}")\n'
            "RunnerLogic.runPytestAndExit(\n"
            f'    r"{path}", r"{json_report_path.as_posix()}", runSettings\n'
            ")\n"
        )

        with open(file_path, "w") as f:
            f.write(file_content)

        return file_path, json_report_path

    def updateTemFilePaths(self) -> Tuple[Path, Path, Path]:
        json_report_path = Path(self.tmp_path).joinpath(f"pytest_file_{self.i_test_file}.json")
        file_path = Path(self.tmp_path).joinpath(f"pytest_file_{self.i_test_file}.py")
        run_settings_path = Path(self.tmp_path).joinpath(f"pytest_run_settings_{self.i_test_file}.json")
        self.i_test_file += 1
        return file_path, json_report_path, run_settings_path
