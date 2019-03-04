# show the tilepile window
import PySide2 as ps
from PySide2 import QtGui, QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from . import window



def start():
    m = window.TilePileUI()
    m.show()
    return m

def main():
    app = QtWidgets.QApplication.instance()
    window = start()
    return window

if __name__ == "__main__":
    eyy = main()
