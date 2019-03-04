from PySide2 import QtGui, QtCore, QtWidgets



class TileListPopup(QtWidgets.QWidget):
    def __init__(self):
        super(TileListPopup, self).__init__(self)

    def paintEvent(self, e):
        dc = QtGui.QPainter(self)
        dc.drawLine(0, 0, 100, 100)
        dc.drawLine(100, 0, 0, 100)
