from pathlib import Path
from typing import Optional

import qt
import slicer

from .EnsureRequirements import ensureRequirements
from .IconPath import icon
from .QWidget import QWidget
from .Results import Results
from .RunnerLogic import RunnerLogic
from .Settings import ModuleSettings, RunSettings
from .SettingsDialog import SettingsDialog
from .TreeView import TreeView


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
        super().__init__(parent)

        self.runProcess = qt.QProcess()
        self.runProcess.finished.connect(self.onProcessFinished)
        self.runProcess.started.connect(self.onProcessStarted)

        self.resultsPath: Optional[Path] = None

        self.dirPathLineEdit = ctk.ctkPathLineEdit(self)
        self.dirPathLineEdit.filters = ctk.ctkPathLineEdit.Dirs
        self.dirPathLineEdit.setToolTip("Path to the directory containing the tests.")

        self.filePatternLineEdit = qt.QLineEdit(self)
        self.filePatternLineEdit.setPlaceholderText("test_*.py")
        self.filePatternLineEdit.setToolTip("Filter test files matching this pattern.")

        self.functionPatternLineEdit = qt.QLineEdit(self)
        self.functionPatternLineEdit.setPlaceholderText("test_ and not test_2")
        self.functionPatternLineEdit.setToolTip(
            "Filter patterns matching input (including classes and functions).\n"
            "Uses pytest's -k filtering option."
        )

        self.treeView = TreeView(self)
        self.logic = RunnerLogic()

        layout = qt.QVBoxLayout(self)

        self.runButton = qt.QPushButton()
        self.runButton.setIcon(icon("test_start_icon.png"))
        self.runButton.clicked.connect(self.onRunTests)
        self.runButton.setToolTip("Runs all the tests in directory matching given patterns.")

        self.collectButton = qt.QPushButton()
        self.collectButton.setIcon(icon("test_collect_icon.png"))
        self.collectButton.clicked.connect(self.onCollectTests)
        self.collectButton.setToolTip("Lists all the tests in directory matching given patterns without running them.")

        self.stopButton = qt.QPushButton()
        self.stopButton.setIcon(icon("test_stop_icon.png"))
        self.stopButton.clicked.connect(self.onStopProcess)
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

        buttonLayout = qt.QHBoxLayout()
        buttonLayout.addWidget(self.runButton)
        buttonLayout.addWidget(self.collectButton)
        buttonLayout.addWidget(self.stopButton)
        buttonLayout.addWidget(showPassedButton)
        buttonLayout.addWidget(showIgnoredButton)
        buttonLayout.addWidget(showCollectedButton)
        buttonLayout.addWidget(settingsButton)
        buttonLayout.addStretch()

        filePatternLayout = qt.QHBoxLayout()
        filePatternLayout.addWidget(self.filePatternLineEdit)
        filePatternLayout.addWidget(self.functionPatternLineEdit)

        self.testResultTextEdit = qt.QTextEdit()
        self.testResultTextEdit.setAcceptRichText(True)
        self.testResultTextEdit.setReadOnly(True)
        self.testResultTextEdit.setLineWrapMode(qt.QTextEdit.NoWrap)
        self.treeView.currentCaseTextChanged.connect(self.testResultTextEdit.setText)

        # Populate the module layout
        layout.addWidget(self.dirPathLineEdit)
        layout.addLayout(filePatternLayout)
        layout.addLayout(buttonLayout)
        layout.addWidget(self.treeView, 2)
        layout.addWidget(self.testResultTextEdit, 1)

        # Update UI with previous settings
        self.restorePreviousSettings(showCollectedButton, showIgnoredButton, showPassedButton)

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
        self._startTestProcess(doCollectOnly=False)

    def onCollectTests(self):
        self._startTestProcess(doCollectOnly=True)

    def _startTestProcess(self, doCollectOnly):
        testDir = Path(self.dirPathLineEdit.currentPath)
        if not testDir.exists():
            slicer.util.warningDisplay(f"Selected test folder doesn't exist: \n{testDir.as_posix()}")
            return

        self.saveSettings()
        self.testResultTextEdit.clear()
        self.treeView.clear()
        self.treeView.setCurrentWidgetToLoading()
        slicer.app.processEvents()

        # Install pytest requirements if needed
        try:
            ensureRequirements()
        except Exception: # noqa
            import traceback
            slicer.util.errorDisplay("Failed to install module dependencies", detailedText=traceback.format_exc())
            self.onProcessFinished()
            return

        runSettings = ModuleSettings().lastRunSettings
        runSettings.extraPytestArgs += [
            *RunSettings.pytestPatternFilterArgs(self.functionPatternLineEdit.text),
            *RunSettings.pytestFileFilterArgs(self.filePatternLineEdit.text)
        ]
        if not doCollectOnly:
            args, path = self.logic.prepareRun(testDir, runSettings)
        else:
            args, path = self.logic.prepareCollect(testDir, runSettings)

        self.resultsPath = path
        self.logic.startQProcess(self.runProcess, args)

    def onProcessStarted(self):
        self.runButton.setEnabled(False)
        self.collectButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    def onStopProcess(self):
        self.runProcess.terminate()
        self.runProcess.kill()
        self.runProcess.close()

    def onProcessFinished(self, *_):
        self.runButton.setEnabled(True)
        self.collectButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.loadResults(self.resultsPath)

    def loadResults(self, resultsPath):
        self.testResultTextEdit.clear()
        self.treeView.refreshResults(Results.fromReportFile(resultsPath))
        self.treeView.setCurrentWidgetToTreeResults()

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
