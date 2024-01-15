from typing import List

import qt
from .Settings import RunSettings

try:
    QDialog = qt.QDialog
except AttributeError:
    QDialog = object


class SettingsDialog(QDialog):
    def __init__(self, settings: RunSettings, parent=None):
        super().__init__(parent)

        self.setWindowFlags(self.windowFlags() & ~qt.Qt.WindowContextHelpButtonHint)

        self.doCloseSlicerAfterRunCheckBox = qt.QCheckBox()
        self.doCloseSlicerAfterRunCheckBox.setToolTip("If checked, closes Slicer Window after test run is complete.")
        self.doCloseSlicerAfterRunCheckBox.setChecked(settings.doCloseSlicerAfterRun)

        self.doUseMainWindowCheckBox = qt.QCheckBox()
        self.doUseMainWindowCheckBox.setToolTip("If checked, launches tests in a Slicer with main window visbile.")
        self.doUseMainWindowCheckBox.setChecked(settings.doUseMainWindow)

        self.doMinimizeMainWindowCheckBox = qt.QCheckBox()
        self.doMinimizeMainWindowCheckBox.setToolTip("If checked, minimizes main window after it is launched.")
        self.doMinimizeMainWindowCheckBox.setChecked(settings.doMinimizeMainWindow)

        self.extraSlicerArgsLineEdit = qt.QLineEdit()
        self.extraSlicerArgsLineEdit.setToolTip("Comma separated list of extra Slicer args to pass to run.")
        self.extraSlicerArgsLineEdit.setPlaceholderText("--no-splash,--disable-modules,--ignore-slicerrc")
        self.extraSlicerArgsLineEdit.setText(",".join(settings.extraSlicerArgs))

        self.extraPytestArgsLineEdit = qt.QLineEdit()
        self.extraPytestArgsLineEdit.setToolTip("Comma separated list of extra Pytest args to pass to run.")
        self.extraPytestArgsLineEdit.setPlaceholderText("--collect-only,--maxfail=2")
        self.extraPytestArgsLineEdit.setText(",".join(settings.extraPytestArgs))

        formLayout = qt.QFormLayout()
        formLayout.addRow("Close Slicer after run:", self.doCloseSlicerAfterRunCheckBox)
        formLayout.addRow("Use main Window:", self.doUseMainWindowCheckBox)
        formLayout.addRow("Minimize main Window:", self.doMinimizeMainWindowCheckBox)
        formLayout.addRow("Extra Slicer args:", self.extraSlicerArgsLineEdit)
        formLayout.addRow("Extra PyTest args:", self.extraPytestArgsLineEdit)

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
        )

    @classmethod
    def toList(cls, val: str) -> List[str]:
        return [v.strip() for v in val.split(",")]

    def onOkClicked(self):
        self.accept()

    def onCancelClicked(self):
        self.reject()
