import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict
import qt

OptStringList = Optional[List[str]]


class RunSettings:
    """
    Object representing execution settings for a test run.
    """

    def __init__(
            self,
            doCloseSlicerAfterRun: bool = True,
            doUseMainWindow: bool = True,
            doMinimizeMainWindow: bool = True,
            extraSlicerArgs: OptStringList = None,
            extraPytestArgs: OptStringList = None,
            doRunCoverage: bool = False,
            coverageReportFormats: OptStringList = None,
            coverageSources: OptStringList = None,
            coverageFilePath: Optional[str] = None
    ):
        self.doCloseSlicerAfterRun = doCloseSlicerAfterRun
        self.doUseMainWindow = doUseMainWindow
        self.doMinimizeMainWindow = doMinimizeMainWindow
        self.extraSlicerArgs = self._toArgList(extraSlicerArgs)
        self.extraPytestArgs = self._toArgList(extraPytestArgs)
        self.doRunCoverage = doRunCoverage
        self.coverageReportFormats = self._toArgList(coverageReportFormats)

        # Coverage sources and file paths are expected to be None if unset in coverage.py
        # IF set, the values will override configuration file. Otherwise, the configuration file may be used.
        self.coverageSources = self._toArgList(coverageSources) or None
        self.coverageFilePath = coverageFilePath or None

    @staticmethod
    def _toArgList(value: OptStringList) -> List[str]:
        if not value:
            return []
        return [v for v in value if v]

    def asDict(self) -> Dict:
        return {k: v for k, v in vars(self).items() if not k.startswith("_")}

    def toJson(self) -> str:
        return json.dumps(self.asDict())

    def toFile(self, filePath: Path) -> None:
        with open(filePath, "w") as f:
            f.write(self.toJson())

    @classmethod
    def fromJson(cls, jsonStr: str) -> "RunSettings":
        return cls(**json.loads(jsonStr)) if jsonStr else cls()

    @classmethod
    def fromFile(cls, filePath: Path) -> "RunSettings":
        with open(filePath, "r") as f:
            return cls.fromJson(f.read())

    @classmethod
    def pytestFileFilterArgs(cls, filePattern: str) -> List[str]:
        return cls._pytestFilterArgs("python_files", filePattern)

    @classmethod
    def pytestPatternFilterArgs(cls, functionPattern: str) -> List[str]:
        if not functionPattern:
            return []

        return ["-k", functionPattern]

    @classmethod
    def _pytestFilterArgs(cls, filterName: str, filterPattern: str) -> List[str]:
        """
        Returns PyTest args corresponding to the file pattern input filter.
        If the input string is empty or None, keeps default PyTest file patter match.
        """
        if not filterPattern:
            return []

        return ["-o", f"{filterName}='{filterPattern}'"]


class ModuleSettings:
    """
    Ease of access for settings saved / restored after Slicer execution.
    Uses QSettings to store / restore the settings.
    """

    @classmethod
    def _getSetting(cls, name, defaultVal):
        return cls._cast(qt.QSettings().value(f"SlicerPythonTestRunner/{name}", defaultVal), defaultVal)

    @classmethod
    def _setSetting(cls, name, value):
        settings = qt.QSettings()
        settings.setValue(f"SlicerPythonTestRunner/{name}", value)
        settings.sync()

    @classmethod
    def _cast(cls, val, defaultVal):
        import slicer.util
        if isinstance(defaultVal, bool):
            return slicer.util.toBool(val)
        return type(defaultVal)(val)

    @property
    def lastPath(self) -> Path:
        return Path(self._getSetting("lastPath", ""))

    @lastPath.setter
    def lastPath(self, value):
        self._setSetting("lastPath", Path(value).as_posix())

    @property
    def lastFilePattern(self):
        return self._getSetting("lastFilePattern", "")

    @lastFilePattern.setter
    def lastFilePattern(self, value):
        self._setSetting("lastFilePattern", value)

    @property
    def lastFunctionPattern(self):
        return self._getSetting("lastFunctionPattern", "")

    @lastFunctionPattern.setter
    def lastFunctionPattern(self, value):
        self._setSetting("lastFunctionPattern", value)

    @property
    def lastRunSettings(self) -> RunSettings:
        return RunSettings.fromJson(self._getSetting("lastRunSettings", ""))

    @lastRunSettings.setter
    def lastRunSettings(self, value: RunSettings):
        self._setSetting("lastRunSettings", value.toJson())

    @property
    def showPassedChecked(self) -> bool:
        return self._getSetting("showPassedChecked", True)

    @showPassedChecked.setter
    def showPassedChecked(self, value: bool):
        self._setSetting("showPassedChecked", value)

    @property
    def showIgnoredChecked(self) -> bool:
        return self._getSetting("showIgnoredChecked", True)

    @showIgnoredChecked.setter
    def showIgnoredChecked(self, value: bool):
        self._setSetting("showIgnoredChecked", value)

    @property
    def showCollectedChecked(self) -> bool:
        return self._getSetting("showCollectedChecked", True)

    @showCollectedChecked.setter
    def showCollectedChecked(self, value: bool):
        self._setSetting("showCollectedChecked", value)
