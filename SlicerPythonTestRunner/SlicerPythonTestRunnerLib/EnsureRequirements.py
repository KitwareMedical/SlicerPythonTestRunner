def ensureRequirements(quiet=False):
    try:
        import coverage  # noqa
        import junit2htmlreport  # noqa
        import junitparser  # noqa
        import pytest  # noqa
        import pytest_jsonreport  # noqa
    except ImportError:
        import slicer

        if not quiet:
            slicer.util.infoDisplay(
                "This module's dependencies are about to be installed. This can take a few minutes."
            )
        slicer.util.pip_install("-q pytest")
        slicer.util.pip_install("-q pytest-json-report")
        slicer.util.pip_install("-q coverage")
        slicer.util.pip_install("-q junitparser")
        slicer.util.pip_install("-q junit2html")
        slicer.util.pip_install("-q pytest-html")
        slicer.util.pip_install("-q pytest-html-merger")
