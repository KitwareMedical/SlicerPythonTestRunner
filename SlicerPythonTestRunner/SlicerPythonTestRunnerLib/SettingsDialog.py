from typing import List

from .QWidget import QDialog
from .Settings import RunSettings


def create_checkbox(tooltip, isChecked):
    import qt

    checkbox = qt.QCheckBox()
    checkbox.setToolTip(tooltip)
    checkbox.setChecked(isChecked)
    return checkbox


def create_text_list_line_edit(tooltip, placeholder, textArgs):
    import qt

    line_edit = qt.QLineEdit()
    line_edit.setToolTip(tooltip)
    line_edit.setPlaceholderText(placeholder)

    textArgs = textArgs or []
    if isinstance(textArgs, str):
        textArgs = [textArgs]

    line_edit.setText(",".join(textArgs))
    return line_edit


class SettingsDialog(QDialog):
    def __init__(self, settings: RunSettings, parent=None):
        import qt

        super().__init__(parent)

        self.setWindowFlags(self.windowFlags() & ~qt.Qt.WindowContextHelpButtonHint)

        self.doCloseSlicerAfterRunCheckBox = create_checkbox(
            tooltip="If checked, closes Slicer Window after test run is complete.",
            isChecked=settings.doCloseSlicerAfterRun,
        )

        self.doUseMainWindowCheckBox = create_checkbox(
            tooltip="If checked, launches tests in a Slicer with main window visible.",
            isChecked=settings.doUseMainWindow,
        )

        self.doMinimizeMainWindowCheckBox = create_checkbox(
            tooltip="If checked, minimizes main window after it is launched.",
            isChecked=settings.doMinimizeMainWindow,
        )

        self.nParallelInstances = qt.QSpinBox()
        self.nParallelInstances.value = settings.nParallelInstances
        self.nParallelInstances.toolTip = (
            "Maximum number of parallel 3D Slicer instances " "launched when parallel run is active."
        )

        self.doRunCoverageCheckBox = create_checkbox(
            tooltip="If checked, launches test coverage for given folder.\n"
            "Coverage will use the local .coveragerc file if any is present.",
            isChecked=settings.doRunCoverage,
        )

        self.extraSlicerArgsLineEdit = create_text_list_line_edit(
            tooltip="Comma separated list of extra Slicer args to pass to run.",
            placeholder="--no-splash,--disable-modules,--ignore-slicerrc",
            textArgs=settings.extraSlicerArgs,
        )

        self.extraPytestArgsLineEdit = create_text_list_line_edit(
            tooltip="Comma separated list of extra Pytest args to pass to run.",
            placeholder="--collect-only,--maxfail=2",
            textArgs=settings.extraPytestArgs,
        )

        self.coverageReportFormatsLineEdit = create_text_list_line_edit(
            tooltip="Comma separated list of formats for the output reports.",
            placeholder="html,xml,lcov",
            textArgs=settings.coverageReportFormats,
        )

        self.coverageSourcesLineEdit = create_text_list_line_edit(
            tooltip="Comma separated list of source paths to scan for test coverage.",
            placeholder="src,my_lib",
            textArgs=settings.coverageSources,
        )

        self.coverageFilePathLineEdit = create_text_list_line_edit(
            tooltip="File path to the report file to generate",
            placeholder="my_report.xml",
            textArgs=settings.coverageFilePath,
        )

        formLayout = qt.QFormLayout()
        formLayout.addRow("Close Slicer after run:", self.doCloseSlicerAfterRunCheckBox)
        formLayout.addRow("Use main Window:", self.doUseMainWindowCheckBox)
        formLayout.addRow("Minimize main Window:", self.doMinimizeMainWindowCheckBox)
        formLayout.addRow("Max Slicer instances:", self.nParallelInstances)
        formLayout.addRow(qt.QLabel(""))
        formLayout.addRow("Extra Slicer args:", self.extraSlicerArgsLineEdit)
        formLayout.addRow("Extra PyTest args:", self.extraPytestArgsLineEdit)
        formLayout.addRow(qt.QLabel(""))
        formLayout.addRow("Run test coverage:", self.doRunCoverageCheckBox)
        formLayout.addRow("Coverage report formats:", self.coverageReportFormatsLineEdit)
        formLayout.addRow("Coverage sources:", self.coverageSourcesLineEdit)
        formLayout.addRow("Coverage path:", self.coverageFilePathLineEdit)

        self.okButton = qt.QPushButton("Ok")
        self.okButton.clicked.connect(self.onOkClicked)

        self.cancelButton = qt.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.onCancelClicked)

        buttonLayout = qt.QHBoxLayout()
        buttonLayout.addStretch()
        buttonLayout.addWidget(self.okButton)
        buttonLayout.addWidget(self.cancelButton)

        vLayout = qt.QVBoxLayout(self)
        vLayout.addLayout(formLayout)
        vLayout.addStretch()
        vLayout.addLayout(buttonLayout)

    def getRunSettings(self) -> RunSettings:
        return RunSettings(
            doCloseSlicerAfterRun=self.doCloseSlicerAfterRunCheckBox.isChecked(),
            doUseMainWindow=self.doUseMainWindowCheckBox.isChecked(),
            doMinimizeMainWindow=self.doMinimizeMainWindowCheckBox.isChecked(),
            extraSlicerArgs=self.toList(self.extraSlicerArgsLineEdit.text),
            extraPytestArgs=self.toList(self.extraPytestArgsLineEdit.text),
            doRunCoverage=self.doRunCoverageCheckBox.isChecked(),
            coverageReportFormats=self.toList(self.coverageReportFormatsLineEdit.text),
            coverageSources=self.toList(self.coverageSourcesLineEdit.text),
            coverageFilePath=self.coverageFilePathLineEdit.text or None,
            nParallelInstances=self.nParallelInstances.value,
        )

    @classmethod
    def toList(cls, val: str) -> List[str]:
        return [v.strip() for v in val.split(",")]

    def onOkClicked(self):
        self.accept()

    def onCancelClicked(self):
        self.reject()
