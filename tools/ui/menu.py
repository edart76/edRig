from PySide2 import QtWidgets, QtGui, QtCore

from edRig.tilepile.ui2.lib import MyDockingUI, dock_window

from edRig import core, deformer


def show():
	#eyy = TilePileUI()
	#eyy = TilePileUI(parent=getMayaWindow())
	# maya = getMayaWindow()
	# print "maya is {}".format(maya)
	eyy = dock_window(EdRigMenu)
	eyyyyy = eyy.show()
	return eyyyyy

class EdRigMenu(MyDockingUI):
	"""base menu for any random stuff I need"""
	CONTROL_NAME = "edRig"
	DOCK_LABEL_NAME = "edRig"