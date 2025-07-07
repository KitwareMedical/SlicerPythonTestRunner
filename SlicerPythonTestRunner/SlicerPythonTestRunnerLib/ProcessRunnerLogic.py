from enum import Enum, auto, unique
from pathlib import Path
from queue import Queue
from time import sleep
from typing import Callable, Optional

import slicer

from .RunnerLogic import Results, RunnerLogic, RunSettings
from .Settings import ModuleSettings
from .Signal import Signal


class TestProcess:
    """
    Wrapper around a QProcess and keeping the information of the results dir.
    """

    def __init__(self, args, path):
        self.processStarted = Signal()
        self.processFinished = Signal(TestProcess)
        self.resultsAvailable = Signal(TestProcess, Path)

        self._args = args
        self._path = path
        self._initProcess()

    def __del__(self):
        self._process.deleteLater()

    def _initProcess(self):
        import qt

        self._process = qt.QProcess()
        self._process.finished.connect(self.onProcessFinished)

    def start(self):
        self._process.start(self._args[0], self._args[1:])
        self.processStarted()

    def stop(self):
        import psutil

        # Stop children process first
        parent = psutil.Process(self._process.processId())
        for child in parent.children(recursive=True):
            child.kill()

        # Stop process itself
        self._process.kill()
        self._process.close()
        self._process.deleteLater()
        self._initProcess()

    def onProcessFinished(self, *_):
        self.resultsAvailable(self, self._path)
        self.processFinished(self)


class ProcessPool:
    """
    Class responsible for the management of the test processes.
    """

    def __init__(self):
        self.processFinished = Signal()

        self._processes: list[TestProcess] = []
        self._queuedProcesses: list[TestProcess] = []
        self._poolSize = 1
        self._isStopping = False

    @property
    def nQueued(self):
        return len(self._queuedProcesses)

    @property
    def nRunning(self):
        return len(self._processes)

    def setPoolSize(self, poolSize):
        self._poolSize = max(1, poolSize)
        self._startNext()

    def addProcess(self, args, path, resultsAvailableCallback: Callable):
        if self._isStopping:
            return

        def processResults(p, results):
            if p not in self._processes:
                return
            resultsAvailableCallback(results)

        process = TestProcess(args, path)
        process.processFinished.connect(self.onProcessFinished)
        process.resultsAvailable.connect(processResults)
        self._queuedProcesses.append(process)
        self._startNext()

    def stop(self):
        self._isStopping = True
        try:
            for proc in self._processes:
                proc.stop()
            self._queuedProcesses.clear()
            self._processes.clear()
        finally:
            self._isStopping = False
            self.processFinished()

    def isFinished(self):
        return not self._queuedProcesses and not self._processes

    def onProcessFinished(self, proc):
        if proc not in self._processes:
            return

        self._processes.remove(proc)
        self._startNext()
        if self.isFinished():
            self.processFinished()

    def _startNext(self):
        while self._canStartNext():
            proc = self._queuedProcesses.pop(0)
            proc.start()
            self._processes.append(proc)

    def _canStartNext(self):
        return self._queuedProcesses and len(self._processes) < self._poolSize and not self._isStopping

    def waitForFinished(self):
        while not self.isFinished():
            sleep(0.1)
            slicer.app.processEvents(0.1)


@unique
class _State(Enum):
    COLLECT_ONLY = auto()
    COLLECT_TESTS = auto()
    TESTING = auto()
    STOPPING = auto()
    IDLE = auto()


class ProcessRunnerLogic:
    """
    Responsible for running the test logic in a process pool.
    """

    def __init__(self):
        self.runnerQueue = Queue()
        self.runningProcesses = []
        self.logic = RunnerLogic()
        self.processFinished = Signal()
        self.processStarted = Signal()
        self.resultsAvailable = Signal(Path)
        self.progressUpdate = Signal(int, int, str)
        self._nResults = 0
        self._iResult = 0

        self._functionPattern: str = ""
        self._filePattern: str = ""
        self._state = _State.IDLE

        self._pool = ProcessPool()
        self._pool.processFinished.connect(self.onPoolFinished)

        self._runSettings: Optional[RunSettings] = None
        self._testDir = None

    def stopTests(self):
        self._state = _State.STOPPING
        self._pool.stop()

    def startTest(
        self, *, testDir: Path, functionPattern: str, filePattern: str, runSettings: RunSettings, doCollectOnly: bool
    ):
        self._runSettings = runSettings
        self._testDir = testDir
        self._functionPattern = functionPattern
        self._filePattern = filePattern

        self._pool.setPoolSize(runSettings.nParallelInstances)
        self._iResult = 0
        self._nResults = 1

        if doCollectOnly:
            self._startCollect()
        else:
            if not self._runSettings.doRunTestFilesIndependently:
                self._startTest()
            else:
                self._startCollect(resultsAvailableCallback=self._startCollected)

        self.processStarted()

    def _startCollected(self, resultsPath: Path):
        filePaths = Results.fromReportFile(resultsPath).getFilePathList()
        if not filePaths:
            self._state = _State.IDLE
            self.processFinished()
            self._reportProgress()
            return

        self._nResults = len(filePaths)
        for filePath in filePaths:
            self._startTest(filePath)

    def _startTest(self, filePattern=None):
        self._state = _State.TESTING
        return self._startProcess(self._testDir, self.logic.prepareRun, filePattern or self._filePattern)

    def _startProcess(
        self,
        testDir,
        prepareF,
        filePattern,
        resultsAvailableCallback: Optional[Callable] = None,
    ):
        args, path = prepareF(testDir, self._getRunSettings(filePattern))
        self._pool.addProcess(args, path, resultsAvailableCallback or self.onResultsAvailable)
        self._reportProgress()

    def _getRunSettings(self, filePattern: str) -> RunSettings:
        runSettings = ModuleSettings().lastRunSettings
        runSettings.extraPytestArgs += [
            *RunSettings.pytestPatternFilterArgs(self._functionPattern),
            *RunSettings.pytestFileFilterArgs(filePattern),
        ]
        return runSettings

    def _startCollect(self, resultsAvailableCallback=None):
        self._state = _State.COLLECT_ONLY if resultsAvailableCallback is None else _State.COLLECT_TESTS
        return self._startProcess(
            self._testDir,
            self.logic.prepareCollect,
            self._filePattern,
            resultsAvailableCallback,
        )

    def waitForFinished(self):
        while self._state != _State.IDLE:
            self.sleepThread_s(0.1)

    def onResultsAvailable(self, results: Path):
        self._iResult += 1
        self.resultsAvailable(results)
        self._reportProgress()

    def _reportProgress(self):
        self.progressUpdate(self._iResult, self._nResults, self._progressStage)

    def writeCoverage(self):
        self.logic.writeCoverageReport(self._testDir, self._runSettings)

    def onPoolFinished(self):
        if self._state not in [_State.IDLE, _State.COLLECT_TESTS]:
            self._state = _State.IDLE
            self.processFinished()

    @property
    def _progressStage(self):
        collectingTests = "collecting tests"
        return {
            _State.TESTING: "running tests",
            _State.COLLECT_ONLY: collectingTests,
            _State.COLLECT_TESTS: collectingTests,
        }.get(self._state, "")

    @classmethod
    def sleepThread_s(cls, sleep_s):
        """
        Sleeps current thread while not blocking Qt interaction.
        """
        import qt

        class _Wait:
            is_waiting = True

        w = _Wait()

        def toggle_wait():
            w.is_waiting = False

        sleep_ms = sleep_s * 1000
        qt.QTimer.singleShot(sleep_ms, toggle_wait)
        while w.is_waiting:
            slicer.app.processEvents(qt.QEventLoop.AllEvents, sleep_ms)
