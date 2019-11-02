
# build the tesserae window
from PySide2 import QtGui, QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.ui2.statuspane import StatusPane
from edRig.tesserae.ui2.lib import  MyDockingUI, dock_window
from edRig.tesserae.ui2.tilesettings import TileSettings
from edRig.lib.python import AbstractTree, testTree



def show():
	#eyy = TilePileUI()
	#eyy = TilePileUI(parent=getMayaWindow())
	# maya = getMayaWindow()
	# print "maya is {}".format(maya)
	eyy = dock_window(TreeTest)
	eyyyyy = eyy.show()
	return eyyyyy


# class TilePileUI(QtWidgets.QWidget):
class TreeTest(MyDockingUI):
	"""main TilePile window"""
	assetChanged = QtCore.Signal(list)
	CONTROL_NAME = "treeTest"
	DOCK_LABEL_NAME = "treeTest"
	def __init__(self, parent=None):
		super(TreeTest, self).__init__(parent)

		self.treeView = TileSettings(self, tree=testTree)
		self.resize(self.treeView.width(), self.treeView.height())

