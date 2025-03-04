import sys
from functools import wraps
from pathlib import Path

from .Settings import RunSettings


def isRunningInSlicerGui() -> bool:
    """
    Returns True if Slicer App exists (Slicer GUI context). False otherwise.
    """
    try:
        import slicer

        return slicer.app is not None
    except (ImportError, AttributeError):
        return False


def isRunningInTestMode() -> bool:
    """
    Returns True is Slicer is running in test mode (CI). False otherwise.
    """
    try:
        import slicer

        return slicer.app.testingEnabled()
    except (ImportError, AttributeError):
        return False


def runTestInSlicerContext(runSettings: RunSettings = None):
    """
    Decorator which allows running the unit test using the SlicerPythonTestRunnerLib if executed using a Slicer Python
    real but not from within a 3D Slicer env.

    Makes running the tests easier in traditional tests runners environments.

    If execution is within the Slicer GUI, running will be done using the current 3D Slicer.
    """
    runSettings = runSettings or RunSettings()

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            from .RunnerLogic import RunnerLogic

            if not isRunningInSlicerGui():
                wrappedFile = Path(sys.modules[f.__module__].__file__)
                wrappedDir = wrappedFile.parent

                results = RunnerLogic().runAndWaitFinished(
                    wrappedDir,
                    RunSettings(
                        doCloseSlicerAfterRun=runSettings.doCloseSlicerAfterRun,
                        doUseMainWindow=runSettings.doUseMainWindow,
                        doMinimizeMainWindow=runSettings.doMinimizeMainWindow,
                        extraPytestArgs=[
                            *RunSettings.pytestFileFilterArgs(wrappedFile.name),
                            *RunSettings.pytestPatternFilterArgs(f.__name__),
                            *runSettings.extraPytestArgs,
                        ],
                        extraSlicerArgs=runSettings.extraSlicerArgs,
                    ),
                )
                if results.failuresNumber:
                    raise AssertionError(f"{f.__name__} execution failed:\n{results.getFailingCasesString()}")
            else:
                return f(*args, **kwargs)

        return wrapper

    return decorator


def skipTestOutsideSlicer(f):
    import pytest

    if not isRunningInSlicerGui():
        pytest.skip(f"Skipping test executed outside Slicer GUI : {f.__name__}")
    return f
