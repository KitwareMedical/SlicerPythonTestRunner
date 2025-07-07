"""
Module responsible for importing QWidget in a way compatible with out of Slicer executions.
"""

try:
    import qt

    QWidget = qt.QWidget
    QDialog = qt.QDialog
    QSortFilterProxyModel = qt.QSortFilterProxyModel

except (AttributeError, ModuleNotFoundError):
    QWidget = object
    QDialog = object
    QSortFilterProxyModel = object
