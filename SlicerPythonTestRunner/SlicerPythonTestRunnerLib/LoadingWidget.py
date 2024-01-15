import qt

from .IconPath import iconPath
from .QWidget import QWidget


class LoadingWidget(QWidget):
    """
    Displays a centered animated loading GIF without stopping.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.loadingGif = qt.QMovie(iconPath("test_loading.gif"))
        self.loadingGif.setScaledSize(qt.QSize(64, 64))
        self.loadingGif.start()
        self.label = qt.QLabel(self)
        self.label.setMovie(self.loadingGif)

        layout = qt.QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.label, 1, qt.Qt.AlignHCenter)
        layout.addStretch()
