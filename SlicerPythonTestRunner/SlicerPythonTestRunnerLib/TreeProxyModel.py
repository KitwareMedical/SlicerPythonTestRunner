from .Case import Outcome
from .QWidget import QSortFilterProxyModel


class TreeProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._showPassed = True
        self._showIgnored = True
        self._showCollected = True

    @property
    def showPassed(self):
        return self._showPassed

    @showPassed.setter
    def showPassed(self, showPassed):
        self._showPassed = showPassed
        self.invalidate()

    @property
    def showCollected(self):
        return self._showCollected

    @showCollected.setter
    def showCollected(self, showCollected):
        self._showCollected = showCollected
        self.invalidate()

    @property
    def showIgnored(self):
        return self._showIgnored

    @showIgnored.setter
    def showIgnored(self, showIgnored):
        self._showIgnored = showIgnored
        self.invalidate()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        import qt

        index = self.sourceModel.index(sourceRow, 0, sourceParent)
        outcome = self.sourceModel.data(index, qt.Qt.UserRole + 1)
        if outcome is None:
            return True

        # Convert outcome back to enum (since Outcome is convertible to int, it is stored as int in model data)
        outcome = Outcome(outcome)

        if outcome.isPassed():
            return self.showPassed

        if outcome.isIgnored():
            return self.showIgnored

        if outcome.isCollected():
            return self.showCollected

        return True
