from pathlib import Path

import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

from SlicerPythonTestRunnerLib import RunnerLogic, RunnerWidget

try:
    import pytest
    import pytest_jsonreport
except ImportError:
    slicer.util.pip_install("pytest")
    slicer.util.pip_install("pytest-json-report")
    import pytest


class SlicerPythonTestRunner(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "Slicer Python Test Runner"
        self.parent.categories = ["Developer Tools"]
        self.parent.dependencies = []
        self.parent.contributors = ["Thibault Pelletier (Kitware)"]
        self.parent.helpText = (
            "This module allows running 3D Slicer module's unit tests directly from 3D Slicer's UI.<br><br>"
            "It uses PyTest to discover the unit tests in a given directory or file and runs the tests in a separate "
            "3D Slicer process.<br>"
            "After the tests have been run, the results are displayed in the UI.<br><br>"
            "The plugin also provides decorators to help running unit tests directly in your favorite IDEs.\n"
            'Learn more on our <a href="https://github.com/KitwareMedical/SlicerPythonTestRunnerExtension">'
            'github page</a>'
        )
        self.parent.acknowledgementText = ""


class SlicerPythonTestRunnerWidget(ScriptedLoadableModuleWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        super().setup()
        self.layout.addWidget(RunnerWidget())


class SlicerPythonTestRunnerTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

        currentDirTest = Path(__file__).parent.joinpath("Testing")
        results = RunnerLogic().runAndWaitFinished(currentDirTest, runSettings)

        if results.failuresNumber:
            slicer.util.errorDisplay(f"Test failed :\n{results.getFailingCasesString()}")
        else:
            slicer.util.delayDisplay("Test OK")

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
