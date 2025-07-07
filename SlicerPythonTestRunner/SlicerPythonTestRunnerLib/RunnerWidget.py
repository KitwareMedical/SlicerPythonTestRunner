from pathlib import Path
from tempfile import TemporaryDirectory

import slicer

from .EnsureRequirements import ensureRequirements
from .ExportDialog import ExportDialog, ExportLogic
from .IconPath import icon
from .LoadingWidget import LoadingIcon
from .ProcessRunnerLogic import ProcessRunnerLogic
from .QWidget import QWidget
from .Results import Results
from .Settings import ModuleSettings
from .SettingsDialog import SettingsDialog
from .TreeView import TreeView


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        import qt

        super().__init__(parent)

        self._progressLabel = qt.QLabel()
        layout = qt.QHBoxLayout(self)
        layout.addWidget(LoadingIcon(iconSize=16, parent=self))
        layout.addWidget(self._progressLabel)
        layout.addStretch()

    def setProgressText(self, text):
        self._progressLabel.text = text


class RunnerWidget(QWidget):
    """
    Test runner widget containing:
        - a directory path edit.
        - test pattern filter line edits.
        - Run, Stop, Settings, etc. toolbar buttons
        - test result tree view.
        - test results text edit.
    """

    def __init__(self, parent=None):
        import ctk
        import qt

        super().__init__(parent)

        self.dirPathLineEdit = ctk.ctkPathLineEdit(self)
        self.dirPathLineEdit.filters = ctk.ctkPathLineEdit.Dirs
        self.dirPathLineEdit.setToolTip("Path to the directory containing the tests.")

        self.filePatternLineEdit = qt.QLineEdit(self)
        self.filePatternLineEdit.setPlaceholderText("test_*.py")
        self.filePatternLineEdit.setToolTip("Filter test files matching this pattern.")

        self.functionPatternLineEdit = qt.QLineEdit(self)
        self.functionPatternLineEdit.setPlaceholderText("test_ and not test_2")
        self.functionPatternLineEdit.setToolTip(
            "Filter patterns matching input (including classes and functions).\n" "Uses pytest's -k filtering option."
        )

        self.treeView = TreeView(self)
        self.logic = ProcessRunnerLogic()
        self.logic.processStarted.connect(self.onProcessStarted)
        self.logic.processFinished.connect(self.onProcessFinished)
        self.logic.resultsAvailable.connect(self.onResultsAvailable)
        self.logic.progressUpdate.connect(self.onProgressUpdate)

        layout = qt.QVBoxLayout(self)

        self.runButton = qt.QPushButton()
        self.runButton.setIcon(icon("test_start_icon.png"))
        self.runButton.clicked.connect(self.onRunTests)
        self.runButton.setToolTip("Runs all the tests in directory matching given patterns.")

        self.parallelRunButton = qt.QPushButton()
        self.parallelRunButton.setIcon(icon("test_parallel_start_icon.png"))
        self.parallelRunButton.clicked.connect(self.onParallelRunTests)
        self.parallelRunButton.setToolTip("Runs all the tests in parallel in directory matching given patterns.")

        self.collectButton = qt.QPushButton()
        self.collectButton.setIcon(icon("test_collect_icon.png"))
        self.collectButton.clicked.connect(self.onCollectTests)
        self.collectButton.setToolTip("Lists all the tests in directory matching given patterns without running them.")

        self.stopButton = qt.QPushButton()
        self.stopButton.setIcon(icon("test_stop_icon.png"))
        self.stopButton.clicked.connect(self.logic.stopTests)
        self.stopButton.setToolTip("Stops the current test execution.")
        self.stopButton.setEnabled(False)

        showPassedButton = qt.QPushButton()
        showPassedButton.setIcon(icon("show_passed_icon.png"))
        showPassedButton.toggled.connect(self.onToggleShowPassed)
        showPassedButton.setCheckable(True)
        showPassedButton.setToolTip("Show Passed")

        showIgnoredButton = qt.QPushButton()
        showIgnoredButton.setIcon(icon("show_ignored_icon.png"))
        showIgnoredButton.toggled.connect(self.onToggleShowIgnored)
        showIgnoredButton.setCheckable(True)
        showIgnoredButton.setToolTip("Show Ignored")

        showCollectedButton = qt.QPushButton()
        showCollectedButton.setIcon(icon("test_collect_icon.png"))
        showCollectedButton.toggled.connect(self.onToggleShowCollected)
        showCollectedButton.setCheckable(True)
        showCollectedButton.setToolTip("Show Collected")

        settingsButton = qt.QPushButton()
        settingsButton.setIcon(icon("test_module_settings_icon.png"))
        settingsButton.clicked.connect(self.onSettingsClicked)
        settingsButton.setToolTip("Edit run settings")

        exportResults = qt.QPushButton()
        exportResults.setIcon(icon("test_export.png"))
        exportResults.clicked.connect(self.onExportClicked)
        exportResults.setToolTip("Export test results")

        buttonLayout = qt.QHBoxLayout()
        buttonLayout.addWidget(self.runButton)
        buttonLayout.addWidget(self.parallelRunButton)
        buttonLayout.addWidget(self.collectButton)
        buttonLayout.addWidget(self.stopButton)
        buttonLayout.addWidget(showPassedButton)
        buttonLayout.addWidget(showIgnoredButton)
        buttonLayout.addWidget(showCollectedButton)
        buttonLayout.addWidget(settingsButton)
        buttonLayout.addWidget(exportResults)
        buttonLayout.addStretch()

        filePatternLayout = qt.QHBoxLayout()
        filePatternLayout.addWidget(self.filePatternLineEdit)
        filePatternLayout.addWidget(self.functionPatternLineEdit)

        self.testResultTextEdit = qt.QTextEdit()
        self.testResultTextEdit.setAcceptRichText(True)
        self.testResultTextEdit.setReadOnly(True)
        self.testResultTextEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        self.treeView.currentCaseTextChanged.connect(self.testResultTextEdit.setText)

        self.progressWidget = ProgressWidget()

        # Populate the module layout
        layout.addWidget(self.dirPathLineEdit)
        layout.addLayout(filePatternLayout)
        layout.addLayout(buttonLayout)
        layout.addWidget(self.progressWidget, 0, qt.Qt.AlignHCenter)
        layout.addWidget(self.treeView, 2)
        layout.addWidget(self.testResultTextEdit, 1)

        # Update UI with previous settings
        self.restorePreviousSettings(showCollectedButton, showIgnoredButton, showPassedButton)

        self.resultFiles = []

        self.setProgressVisible(False)

    def setProgressVisible(self, isVisible):
        self.progressWidget.setVisible(isVisible)

    def onProgressUpdate(self, iResult, nResults, stage):
        self.progressWidget.setProgressText(f"Testing in progress... ({stage} {iResult}/{nResults})")

    def restorePreviousSettings(self, showCollectedButton, showIgnoredButton, showPassedButton):
        settings = ModuleSettings()
        self.dirPathLineEdit.currentPath = settings.lastPath
        self.filePatternLineEdit.setText(settings.lastFilePattern)
        self.functionPatternLineEdit.setText(settings.lastFunctionPattern)
        showIgnoredButton.setChecked(settings.showIgnoredChecked)
        showPassedButton.setChecked(settings.showPassedChecked)
        showCollectedButton.setChecked(settings.showCollectedChecked)
        self.onToggleShowIgnored(settings.showIgnoredChecked)
        self.onToggleShowPassed(settings.showPassedChecked)
        self.onToggleShowCollected(settings.showCollectedChecked)

    def saveSettings(self):
        settings = ModuleSettings()
        settings.lastPath = self.dirPathLineEdit.currentPath
        settings.lastFilePattern = self.filePatternLineEdit.text
        settings.lastFunctionPattern = self.functionPatternLineEdit.text

    def onRunTests(self):
        self._startTests(doCollectOnly=False)

    def onParallelRunTests(self):
        self._startTests(doCollectOnly=False, doRunTestFilesIndependently=True)

    def onCollectTests(self):
        self._startTests(doCollectOnly=True)

    def _startTests(self, doCollectOnly, doRunTestFilesIndependently=False):
        testDir = Path(self.dirPathLineEdit.currentPath)
        if not testDir.exists():
            slicer.util.warningDisplay(f"Selected test folder doesn't exist: \n{testDir.as_posix()}")
            return

        # Install pytest requirements if needed
        try:
            ensureRequirements()
        except Exception:  # noqa
            import traceback

            slicer.util.errorDisplay(
                "Failed to install module dependencies",
                detailedText=traceback.format_exc(),
            )
            return

        self.resultFiles.clear()
        self.saveSettings()
        self.testResultTextEdit.clear()
        self.treeView.clear()
        slicer.app.processEvents()

        runSettings = ModuleSettings().lastRunSettings
        runSettings.doRunTestFilesIndependently = doRunTestFilesIndependently
        self.logic.startTest(
            testDir=testDir,
            functionPattern=self.functionPatternLineEdit.text,
            filePattern=self.filePatternLineEdit.text,
            runSettings=runSettings,
            doCollectOnly=doCollectOnly,
        )

    def onProcessStarted(self):
        self.runButton.setEnabled(False)
        self.parallelRunButton.setEnabled(False)
        self.collectButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.setProgressVisible(True)

    def onProcessFinished(self, *_):
        self.logic.writeCoverage()
        self.runButton.setEnabled(True)
        self.parallelRunButton.setEnabled(True)
        self.collectButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.setProgressVisible(False)

    def onResultsAvailable(self, resultsPath: Path):
        self.resultFiles.append(resultsPath)
        self.treeView.appendResults(Results.fromReportFile(resultsPath))

    def onToggleShowPassed(self, isChecked):
        self.treeView.setShowPassed(isChecked)
        ModuleSettings().showPassedChecked = isChecked

    def onToggleShowCollected(self, isChecked):
        self.treeView.setShowCollected(isChecked)
        ModuleSettings().showCollectedChecked = isChecked

    def onToggleShowIgnored(self, isChecked):
        self.treeView.setShowIgnored(isChecked)
        ModuleSettings().showIgnoredChecked = isChecked

    @staticmethod
    def onSettingsClicked():
        settings = ModuleSettings()
        settingsDialog = SettingsDialog(settings.lastRunSettings)
        if not settingsDialog.exec():
            return

        settings.lastRunSettings = settingsDialog.getRunSettings()

    def onExportClicked(self):
        with TemporaryDirectory() as tmpDir:
            combinedXmlFile, combinedHtmlFile = self.combineReportFiles(tmpDir)

            if not combinedXmlFile.is_file():
                slicer.util.warningDisplay("No results found to export")
                return

            exportDialog = ExportDialog(combinedXmlFile, combinedHtmlFile, Path(self.dirPathLineEdit.currentPath))
            exportDialog.exec()

    def _combineXmlResultFiles(self, filePath):
        ExportLogic.combineXmlReportFiles(ExportLogic.getXmlReportFilesFromJSonList(self.resultFiles), filePath)

    def _combineHtmlResultFiles(self, filePath):
        ExportLogic.combineHtmlReportFiles(ExportLogic.getHtmlReportFilesFromJsonList(self.resultFiles), filePath)

    def combineReportFiles(self, destDir):
        destDir = Path(destDir)
        combinedXmlFile = destDir / "test_report.xml"
        self._combineXmlResultFiles(combinedXmlFile)

        combinedHtmlFile = destDir / "test_report.html"
        self._combineHtmlResultFiles(combinedHtmlFile)

        if not combinedHtmlFile.is_file():
            ExportLogic.convertJunitXmlToHtml(combinedXmlFile, combinedHtmlFile)

        return combinedXmlFile, combinedHtmlFile

    def waitForFinished(self):
        self.logic.waitForFinished()
