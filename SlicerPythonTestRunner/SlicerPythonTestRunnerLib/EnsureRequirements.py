def _ensureRequirements():
    try:
        import pytest
        import pytest_jsonreport
        import coverage
    except ImportError:
        import slicer
        slicer.util.pip_install("-q pytest")
        slicer.util.pip_install("-q pytest-json-report")
        slicer.util.pip_install("-q coverage")


_ensureRequirements()
