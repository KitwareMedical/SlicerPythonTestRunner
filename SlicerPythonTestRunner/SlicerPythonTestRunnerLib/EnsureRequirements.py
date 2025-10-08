def ensureRequirements(quiet=False):
    try:
        import coverage  # noqa
        import junit2htmlreport  # noqa
        import junitparser  # noqa
        import psutil  # noqa
        import pytest  # noqa
        import pytest_jsonreport  # noqa
    except ImportError:
        import slicer

        if not quiet:
            slicer.util.infoDisplay(
                "This module's dependencies are about to be installed. This can take a few minutes."
            )
        slicer.util.pip_install("--root-user-action=ignore -q pytest")
        slicer.util.pip_install("--root-user-action=ignore -q pytest-json-report")
        slicer.util.pip_install("--root-user-action=ignore -q coverage")
        slicer.util.pip_install("--root-user-action=ignore -q junitparser")
        slicer.util.pip_install("--root-user-action=ignore -q junit2html")
        slicer.util.pip_install("--root-user-action=ignore -q pytest-html")
        slicer.util.pip_install("--root-user-action=ignore -q pytest-html-merger")
        slicer.util.pip_install("--root-user-action=ignore -q psutil")
