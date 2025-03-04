import qt

from .IconPath import iconPath
from .QWidget import QWidget


class LoadingIcon(QWidget):
    def __init__(self, iconSize, parent=None):
        super().__init__(parent)

        layout = qt.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.loadingGif = qt.QMovie(iconPath("test_loading.gif"))
        self.loadingGif.setScaledSize(qt.QSize(iconSize, iconSize))
        self.loadingGif.start()

        self.label = qt.QLabel(self)
        self.label.setMovie(self.loadingGif)
        layout.addWidget(self.label)


class LoadingWidget(QWidget):
    """
    Displays a centered animated loading GIF without stopping.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = qt.QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(LoadingIcon(iconSize=64, parent=self), 1, qt.Qt.AlignHCenter)
        layout.addStretch()
