def _ensureRequirements():
    try:
        import pytest
        import pytest_jsonreport
    except ImportError:
        import slicer
        slicer.util.pip_install("pytest")
        slicer.util.pip_install("pytest-json-report")


_ensureRequirements()
