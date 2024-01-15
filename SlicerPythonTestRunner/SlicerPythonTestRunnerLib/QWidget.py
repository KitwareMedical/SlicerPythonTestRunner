"""
Module responsible for importing QWidget in a way compatible with out of Slicer executions.
"""

try:
    import qt

    QWidget = qt.QWidget
except AttributeError:
    QWidget = object
