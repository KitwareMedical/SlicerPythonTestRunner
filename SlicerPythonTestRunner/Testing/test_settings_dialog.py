from SlicerPythonTestRunnerLib import runTestInSlicerContext, RunSettings, SettingsDialog
import slicer


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_settings_dialog_can_be_displayed():
    d = SettingsDialog(RunSettings())
    d.show()
    slicer.app.processEvents()


@runTestInSlicerContext(RunSettings(doUseMainWindow=False, extraSlicerArgs=["--disable-modules"]))
def test_a_settings_dialog_can_convert_to_and_from_run_settings():
    exp_settings = RunSettings(
        doCloseSlicerAfterRun=True,
        doUseMainWindow=False,
        doMinimizeMainWindow=True,
        extraSlicerArgs=["1", "2"],
        extraPytestArgs=["3", "4"],
        doRunCoverage=False,
        coverageReportFormats=["html", "xml"],
        coverageSources=["5"],
        coverageFilePath="html/folder"
    )
    d = SettingsDialog(exp_settings)
    s = d.getRunSettings()
    assert s.asDict() == exp_settings.asDict()
