from typing import Dict, Optional

import qt

from .Signal import Signal
from .Case import Case, Outcome
from .IconPath import icon
from .LoadingWidget import LoadingWidget
from .QWidget import QWidget
from .Results import Results
from .TreeProxyModel import TreeProxyModel


class TreeView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.currentCaseTextChanged = Signal("str")

        self.stack = qt.QStackedWidget()

        self.loading = LoadingWidget(self.stack)
        self.tree = qt.QTreeView(self.stack)
        self.tree.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        self.tree.clicked.connect(self.onItemClicked)
        self.tree.setEditTriggers(qt.QAbstractItemView.NoEditTriggers)
        self.treeModel = qt.QStandardItemModel()
        self.treeProxyModel = TreeProxyModel()
        self.treeProxyModel.setSourceModel(self.treeModel)
        self.treeProxyModel.setRecursiveFilteringEnabled(True)
        self.tree.setModel(self.treeProxyModel)

        self.tree.header().setVisible(False)
        self.nodeIdItemDict: Dict[str, qt.QTreeWidgetItem] = {}

        self.resultLabel = qt.QLabel(self)
        self.lastResults = Results("", [])
        self.stack.addWidget(self.loading)
        self.stack.addWidget(self.tree)
        layout = qt.QVBoxLayout(self)
        layout.addWidget(self.resultLabel)
        layout.addWidget(self.stack)
        layout.setContentsMargins(0, 0, 0, 0)
        self.updateResultsLabel()
        self.setCurrentWidgetToTreeResults()

    def clear(self):
        self.refreshResults(Results("", []))

    def getCaseCount(self) -> int:
        cases = [self.getItemData(item) for item in self.nodeIdItemDict.values()]
        return sum([1 for case in cases if case is not None])

    def getDisplayedRowCount(self) -> int:
        return self.getDisplayedIndexRowCount(None)

    def getDisplayedIndexRowCount(self, parentIndex):
        parentIndex = parentIndex or qt.QModelIndex()
        count = self.treeProxyModel.rowCount(parentIndex)
        return count + sum([
            self.getDisplayedIndexRowCount(
                self.treeProxyModel.index(i_child, 0, parentIndex)
            ) for i_child in range(count)
        ])

    def getOutcomes(self) -> Dict[str, Outcome]:
        return {nodeId: self.getItemOutcome(item) for nodeId, item in self.nodeIdItemDict.items()}

    def refreshResults(self, results: Results) -> None:
        self.treeModel.clear()
        self.nodeIdItemDict.clear()
        self.lastResults = results

        for case in results.getAllCases():
            if not self.hasParentItem(case):
                self.createParentItem(case)

            parent = self.getParentItem(case)
            parent.appendRow(self.createCaseItem(case))

        self.updateOutcome()
        self.updateResultsLabel()
        self.treeProxyModel.invalidate()
        self.treeProxyModel.sort(0)

    def updateResultsLabel(self):
        self.resultLabel.setText(
            self.lastResults.getSummaryString() if self.lastResults else "No tests results to display."
        )

    def setCurrentWidgetToTreeResults(self):
        self.stack.setCurrentWidget(self.tree)

    def setCurrentWidgetToLoading(self):
        self.stack.setCurrentWidget(self.loading)

    def hasParentItem(self, case: Case) -> bool:
        return case.getParentID() in self.nodeIdItemDict

    def getParentItem(self, case: Case) -> "qt.QTreeWidgetItem":
        return self.getParent(case.getParentID())

    def hasParentIds(self, parentNodeId: str) -> bool:
        return parentNodeId in self.nodeIdItemDict

    def createParentItem(self, case: Case) -> None:
        self.createAllParentIds(case.getParentID())

    def createAllParentIds(self, caseNodeId: str) -> None:
        if not caseNodeId or caseNodeId in self.nodeIdItemDict:
            return

        parentNodeId = Case.parentID(caseNodeId)
        if not self.hasParentIds(parentNodeId):
            self.createAllParentIds(parentNodeId)

        parent = self.getParent(parentNodeId)
        parent.appendRow(self.createItem(caseNodeId))

    def getParent(self, parentNodeId):
        if parentNodeId not in self.nodeIdItemDict:
            return self.treeModel.invisibleRootItem()
        return self.nodeIdItemDict[parentNodeId]

    def createCaseItem(self, case: Case):
        return self.createItem(case.nodeid, case)

    def createItem(self, caseNodeId: str, case: Optional[Case] = None) -> "qt.QTreeWidgetItem":
        item = qt.QStandardItem()
        item.setText(Case.caseNameFromId(caseNodeId))
        item.setData(case, qt.Qt.UserRole)
        self.nodeIdItemDict[caseNodeId] = item
        return item

    @staticmethod
    def getItemData(item):
        return item.data(qt.Qt.UserRole)

    def updateOutcome(self):
        for item in self.nodeIdItemDict.values():
            outcome = self.getItemOutcome(item)
            item.setIcon(self.getItemIcon(outcome))
            item.setData(outcome, qt.Qt.UserRole + 1)

    @classmethod
    def getItemIcon(cls, outcome: Outcome) -> "qt.QIcon":
        okIcon = icon("test_ok_icon.png")
        failIcon = icon("test_failed_icon.png")
        skipIcon = icon("test_skipped_icon.png")
        collectedIcon = icon("test_collect_icon.png")

        return {
            Outcome.passed: okIcon,
            Outcome.failed: failIcon,
            Outcome.error: failIcon,
            Outcome.unknown: skipIcon,
            Outcome.collected: collectedIcon,
            Outcome.skipped: skipIcon,
            Outcome.xfailed: okIcon,
            Outcome.xpassed: okIcon,
        }.get(outcome, qt.QIcon())

    def getItemOutcome(self, item) -> Outcome:
        outcomes = set()
        if self.getItemData(item) is not None:
            outcomes.add(self.getItemData(item).outcome)

        for i_child in range(item.rowCount()):
            outcomes.add(self.getItemOutcome(item.child(i_child)))

        if not outcomes:
            return Outcome.unknown

        return list(sorted(outcomes))[0]

    def setShowPassed(self, doShowPassed):
        self.treeProxyModel.showPassed = doShowPassed

    def setShowIgnored(self, doShowIgnored):
        self.treeProxyModel.showIgnored = doShowIgnored

    def setShowCollected(self, doShowCollected):
        self.treeProxyModel.showCollected = doShowCollected

    def getDisplayedCases(self, parentIndex):
        parentIndex = parentIndex or qt.QModelIndex()
        parentCase = self.treeProxyModel.data(parentIndex, qt.Qt.UserRole)
        leafCases = [
            case
            for i_child in range(self.treeProxyModel.rowCount(parentIndex))
            for case in self.getDisplayedCases(self.treeProxyModel.index(i_child, 0, parentIndex))
        ]

        return [parentCase] + leafCases if parentCase else leafCases

    def onItemClicked(self, index):
        results = Results(self.lastResults.testRoot, self.getDisplayedCases(index))
        self.currentCaseTextChanged.emit(results.getSummaryString() + "\n\n" + results.getFailingCasesString())
