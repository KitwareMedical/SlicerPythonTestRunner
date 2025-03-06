from pathlib import Path

import slicer
from slicer.ScriptedLoadableModule import (
    ScriptedLoadableModule,
    ScriptedLoadableModuleTest,
    ScriptedLoadableModuleWidget,
)


class SlicerPythonTestRunner(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Slicer Python Test Runner"
        self.parent.categories = ["Developer Tools"]
        self.parent.dependencies = []
        self.parent.contributors = ["Thibault Pelletier (Kitware SAS)"]
        self.parent.helpText = (
            "This module allows running 3D Slicer module's unit tests directly from 3D Slicer's UI.<br><br>"
            "It uses PyTest to discover the unit tests in a given directory or file and runs the tests in a separate "
            "3D Slicer process.<br>"
            "After the tests have been run, the results are displayed in the UI.<br><br>"
            "The plugin also provides decorators to help running unit tests directly in your favorite IDEs.\n"
            'Learn more on our <a href="https://github.com/KitwareMedical/SlicerPythonTestRunner">'
            "github page</a>"
        )
        self.parent.acknowledgementText = (
            "This module was originally developed by Kitware SAS in order to help improve "
            "Slicer modules and Slicer based applications code quality."
        )


class SlicerPythonTestRunnerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        from SlicerPythonTestRunnerLib import RunnerWidget

        super().setup()
        self.layout.addWidget(RunnerWidget())


class SlicerPythonTestRunnerTest(ScriptedLoadableModuleTest):
    def runTest(self):
        """
        Clear scene and run every test in the Testing folder
        """
        from SlicerPythonTestRunnerLib import RunnerLogic, RunSettings

        slicer.mrmlScene.Clear()

        currentDirTest = Path(__file__).parent.joinpath("Testing")
        results = RunnerLogic().runAndWaitFinished(
            currentDirTest, RunSettings(doUseMainWindow=False, doCloseSlicerAfterRun=True)
        )

        if results.failuresNumber:
            raise AssertionError(f"Test failed :\n{results.getFailingCasesString()}")

        ok_msg = f"Test OK : {results.getSummaryString()}"
        print(ok_msg)
        slicer.util.delayDisplay(ok_msg)
