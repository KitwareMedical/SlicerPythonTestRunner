def ensureRequirements():
    try:
        import pytest
        import pytest_jsonreport
        import coverage
    except ImportError:
        import slicer
        slicer.util.infoDisplay("This module's dependencies are about to be installed. This can take a few minutes.")
        slicer.util.pip_install("-q pytest")
        slicer.util.pip_install("-q pytest-json-report")
        slicer.util.pip_install("-q coverage")
