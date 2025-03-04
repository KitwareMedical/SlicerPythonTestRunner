import os.path
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import qt
import slicer.util

try:
    QDialog = qt.QDialog
except AttributeError:
    QDialog = object


class ExportLogic:
    @classmethod
    def getXmlReportFilesFromJSonList(cls, reportFiles: list[Path]) -> list[Path]:
        return cls._getFileFromJsonList(reportFiles, ".xml")

    @classmethod
    def getHtmlReportFilesFromJsonList(cls, reportFiles: list[Path]) -> list[Path]:
        return cls._getFileFromJsonList(reportFiles, ".html")

    @staticmethod
    def _getFileFromJsonList(reportFiles: list[Path], fileExt: str) -> list[Path]:
        files = [f.with_suffix(fileExt) for f in reportFiles]
        files = [f for f in files if f.is_file()]
        return files

    @staticmethod
    def combineXmlReportFiles(reportFiles: list[Path], outFilePath: Path) -> None:
        from junitparser import JUnitXml

        if not reportFiles:
            return

        report = JUnitXml.fromfile(reportFiles[0].as_posix())
        for f in reportFiles[1:]:
            report += JUnitXml.fromfile(f.as_posix())

        report.write(outFilePath.as_posix())

    @staticmethod
    def convertJunitXmlToHtml(filePath: Path, outFilePath: Path) -> None:
        from junit2htmlreport.runner import run

        if not filePath.is_file():
            return

        run([filePath.as_posix(), outFilePath.as_posix()])

    @classmethod
    def combineHtmlReportFiles(cls, reportFiles: list[Path], outFilePath: Path) -> None:
        from pytest_html_merger.main import merge_html_files

        if not reportFiles:
            return

        with TemporaryDirectory() as tmpDir:
            tmpDir = Path(tmpDir)

            cls.copyHtmlAssetsFolder(reportFiles, tmpDir)
            for reportFile in reportFiles:
                cls.copyFile(reportFile, tmpDir / reportFile.name)

            merge_html_files(tmpDir.as_posix(), outFilePath.as_posix(), title="")

    @staticmethod
    def copyFile(srcPath, destPath):
        if os.path.exists(destPath):
            os.remove(destPath)

        shutil.copyfile(srcPath, destPath)

    @classmethod
    def copyHtmlAssetsFolder(cls, reportFiles: list[Path], destDir: Path) -> None:
        if not reportFiles:
            return

        reportFolder = reportFiles[0].parent
        shutil.copytree(reportFolder / "assets", destDir / "assets")

    @classmethod
    def copyReport(cls, xmlFilePath: Path, htmlFilePath: Path, selectedPath: Path) -> None:
        selectedPath.parent.mkdir(parents=True, exist_ok=True)

        if selectedPath.suffix == ".xml":
            cls.copyFile(xmlFilePath, selectedPath)
        else:
            cls.copyFile(htmlFilePath, selectedPath)


class ExportDialog(QDialog):
    """
    Dialog for exporting test results.
    """

    def __init__(self, xmlFilePath: Path, htmlFilePath: Path, defaultDir: Path, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~qt.Qt.WindowContextHelpButtonHint)
        self._xmlFilePath = xmlFilePath
        self._htmlFilePath = htmlFilePath

        exportLayout = qt.QHBoxLayout()

        self.exportPath = qt.QLineEdit()
        self.exportPath.setPlaceholderText("/path/to/report.html")
        self.exportPath.setToolTip("Path to the output report file. Supported formats are XML or HTML")
        self.exportPath.text = Path(defaultDir).joinpath("test_report.html").as_posix()

        pathButton = qt.QPushButton()
        pathButton.setText("...")
        pathButton.clicked.connect(self.onPathButtonClicked)

        exportLayout.addWidget(self.exportPath, 1)
        exportLayout.addWidget(pathButton)

        layout = qt.QVBoxLayout(self)
        layout.addLayout(exportLayout)

        buttonBox = qt.QDialogButtonBox()
        buttonBox.addButton(buttonBox.Cancel)
        buttonBox.addButton(buttonBox.Save)
        buttonBox.rejected.connect(self.reject)
        buttonBox.accepted.connect(self.onAccept)
        layout.addWidget(buttonBox)

    def onPathButtonClicked(self, *_):
        savePath = qt.QFileDialog.getSaveFileName(
            self, "Select report output path", self.exportPath.text, "*.html;;*.xml"
        )
        if not savePath:
            return

        self.exportPath.text = Path(savePath).as_posix()

    def onAccept(self):
        selectedPath = Path(self.exportPath.text)
        if selectedPath.suffix not in [".html", ".xml"]:
            slicer.util.warningDisplay("Unsupported export format. Please select either XML or HTML")
            return

        ExportLogic.copyReport(self._xmlFilePath, self._htmlFilePath, selectedPath)
        self.accept()
