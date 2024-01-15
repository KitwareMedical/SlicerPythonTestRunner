import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict
import qt


class RunSettings:
    """
    Object representing execution settings for a test run.
    """

    def __init__(
            self,
            doCloseSlicerAfterRun: bool = True,
            doUseMainWindow: bool = True,
            doMinimizeMainWindow: bool = True,
            extraSlicerArgs: List[str] = None,
            extraPytestArgs: List[str] = None,
    ):
        self.doCloseSlicerAfterRun = doCloseSlicerAfterRun
        self.doUseMainWindow = doUseMainWindow
        self.doMinimizeMainWindow = doMinimizeMainWindow
        self.extraSlicerArgs = extraSlicerArgs
        self.extraPytestArgs = extraPytestArgs

    @property
    def extraSlicerArgs(self):
        return self._extraSlicerArgs

    @extraSlicerArgs.setter
    def extraSlicerArgs(self, value):
        self._extraSlicerArgs = self._toArgList(value)

    @property
    def extraPytestArgs(self):
        return self._extraPytestArgs

    @extraPytestArgs.setter
    def extraPytestArgs(self, value):
        self._extraPytestArgs = self._toArgList(value)

    @staticmethod
    def _toArgList(value: Optional[List[str]]) -> List[str]:
        if not value:
            return []
        return [v for v in value if v]

    def asDict(self) -> Dict:
        return {
            "doCloseSlicerAfterRun": self.doCloseSlicerAfterRun,
            "doUseMainWindow": self.doUseMainWindow,
            "doMinimizeMainWindow": self.doMinimizeMainWindow,
            "extraSlicerArgs": self.extraSlicerArgs,
            "extraPytestArgs": self.extraPytestArgs,
        }

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
    def pytestClassFilterArgs(cls, classPattern: str) -> List[str]:
        return cls._pytestFilterArgs("python_classes", classPattern)

    @classmethod
    def pytestFunctionFilterArgs(cls, functionPattern: str) -> List[str]:
        return cls._pytestFilterArgs("python_functions", functionPattern)

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
    def lastClassPattern(self):
        return self._getSetting("lastClassPattern", "")

    @lastClassPattern.setter
    def lastClassPattern(self, value):
        self._setSetting("lastClassPattern", value)

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
