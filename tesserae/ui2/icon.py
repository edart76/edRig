
from PySide2 import QtCore, QtGui, QtWidgets
from edRig import CURRENT_PATH

ICON_PATH = CURRENT_PATH + "/resources/icons/"


# square icons
squareCentre = QtGui.QPixmap()
squareCentre.load( ICON_PATH + "squareCentre.png")

squareSides = {}
for i, key in enumerate(["down", "left", "up", "right"]):
	tf = QtGui.QTransform()
	tf.rotate(90 * i)
	squareSides[key] = squareCentre.transformed(tf)
