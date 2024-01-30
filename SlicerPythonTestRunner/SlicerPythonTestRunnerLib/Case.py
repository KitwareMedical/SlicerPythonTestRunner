import re
from dataclasses import dataclass, field
from enum import unique, IntEnum, auto
from typing import List, Dict


@unique
class Outcome(IntEnum):
    """
    Possible test outcomes.
    Enums are sorted to represent the expected outcome if taking the first sorted outcome in list of children.

    For instance, a test suite with children outcomes of [passed, failed, xpassed] should return an aggregated outcome
    of failed.
    """

    unknown = auto()
    error = auto()
    failed = auto()
    skipped = auto()
    passed = auto()
    xpassed = auto()
    xfailed = auto()
    collected = auto()

    def isPassed(self) -> bool:
        return self in self.passedOutcomes()

    def isFailed(self) -> bool:
        return self in self.failedOutcomes()

    def isExecuted(self) -> bool:
        return self in self.executedOutcomes()

    def isIgnored(self) -> bool:
        return self in self.ignoredOutcomes()

    def isCollected(self) -> bool:
        return self in self.collectedOutcomes()

    @staticmethod
    def passedOutcomes() -> List["Outcome"]:
        return [Outcome.passed, Outcome.xfailed, Outcome.xpassed]

    @staticmethod
    def failedOutcomes() -> List["Outcome"]:
        return [Outcome.error, Outcome.failed]

    @staticmethod
    def ignoredOutcomes() -> List["Outcome"]:
        return [Outcome.skipped]

    @staticmethod
    def collectedOutcomes() -> List["Outcome"]:
        return [Outcome.collected]

    @classmethod
    def executedOutcomes(cls) -> List["Outcome"]:
        return cls.passedOutcomes() + cls.failedOutcomes() + cls.ignoredOutcomes()


@dataclass
class Case:
    """
    Container for tests results parsed from JSON report.
    """

    nodeid: str = ""
    outcome: Outcome = Outcome.unknown
    duration: float = 0
    message: str = ""
    stdout: str = ""
    stderr: str = ""
    logs: List[str] = field(default_factory=list)

    @classmethod
    def fromExecutedTestDict(cls, case: Dict) -> "Case":
        try:
            outcome = Outcome[case["outcome"]]
        except KeyError:
            outcome = Outcome.unknown

        caseCall = case.get("call", {})
        return cls(
            outcome=outcome,
            nodeid=case["nodeid"],
            duration=sum([case.get(d, {}).get("duration", 0.) for d in ["setup", "call", "teardown"]]),
            message=caseCall.get("longrepr", ""),
            stdout=caseCall.get("stdout", ""),
            stderr=caseCall.get("stderr", ""),
            logs=[f"[{log['levelname']}] {log['msg']}" for log in caseCall.get("log", [])],
        )

    @classmethod
    def parentID(cls, nodeid: str) -> str:
        return "::".join(cls.nodeIdParts(nodeid)[:-1])

    @classmethod
    def nodeIdParts(cls, nodeid: str) -> List[str]:
        """
        Splits input node id by sub parts.
        Node is expected to be of the shape :
            test_file.py::TestClass::test_fun[Parameterized tests]

        The expected output is :
            [test_file.py, TestClass, test_fun[Parameterized tests]]
        """
        if not nodeid:
            return []

        nodeIdHead = re.split(r"[^a-zA-Z0-9:_./\\\s]", nodeid)[0]
        nodeIdTail = nodeid[len(nodeIdHead):]
        nodeIdParts = nodeIdHead.split("::")
        nodeIdParts[-1] += nodeIdTail

        return nodeIdParts

    @classmethod
    def caseNameFromId(cls, nodeid: str) -> str:
        comp = cls.nodeIdParts(nodeid)
        if not comp:
            return ""
        return comp[-1]

    @staticmethod
    def nodeIdSep() -> str:
        return "::"

    def getParentID(self) -> str:
        return self.parentID(self.nodeid)

    @classmethod
    def fromCollectedTestDict(cls, case: Dict) -> "Case":
        try:
            outcome = Outcome[case.get("outcome", "collected")]
        except KeyError:
            outcome = Outcome.unknown

        return cls(outcome=outcome, nodeid=case["nodeid"], message=case.get("longrepr", ""))

    def getDebugString(self) -> str:
        status_msg = f"\n{self.message}" if self.message else ""
        return (
            f"{self.nodeid} {self.outcome.name.upper()} [{self.outcome.name.upper()}]{status_msg}{self.getLogString()}"
        )

    def getLogString(self):
        if not any([self.stdout, self.stderr, self.logs]):
            return ""

        pad_str = "-" * 40
        logs_str = "\n".join(self.logs)

        return (
            f"\n\n{pad_str}[STD OUT]{pad_str}\n"
            f"{self.stdout}\n\n"
            f"{pad_str}[STD ERR]{pad_str}\n"
            f"{self.stderr}\n\n"
            f"{pad_str}[LOGGING]{pad_str}\n"
            f"{logs_str}"
        )
