# build the tesserae window
from PySide2 import QtGui, QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.ui2.statuspane import StatusPane
from edRig.tesserae.ui2.lib import  MyDockingUI, dock_window
from edRig.pipeline import TempAsset
from edRig import ROOT_PATH



def show():
	#eyy = TilePileUI()
	#eyy = TilePileUI(parent=getMayaWindow())
	# maya = getMayaWindow()
	# print "maya is {}".format(maya)
	eyy = dock_window(TilePileUI)
	eyyyyy = eyy.show()
	return eyyyyy


# class TilePileUI(QtWidgets.QWidget):
class TilePileUI(MyDockingUI):
	"""main TilePile window"""
	assetChanged = QtCore.Signal(list)
	CONTROL_NAME = "TilePile"
	DOCK_LABEL_NAME = "TilePile"
	def __init__(self, parent=None):
		super(TilePileUI, self).__init__(parent)
		self.graphView = None

		self.text = "hello :)"
		self.width = 1400
		self.height = 800

		self.rootPath = ROOT_PATH

		self.initUi()
		self.initSignals()
		self.setWindowModality(QtCore.Qt.WindowModal)
		#self.setWindowFlags(QtCore.Qt.Window)
		self.resize(self.width, self.height)

		self.savePath = None
		self.saveFolder = None

		self.hasChanged = False # for checking saves?

		self._asset = None

		print "tp init finished"

	@property
	def asset(self):
		return self._asset or TempAsset


	def initUi(self):
		"""no windows
		no widgets
		only beautiful boundless nodes"""

		#parent = getMayaWindow()
		#parentWindow = QtWidgets.QMainWindow(parent)
		#self.setText("hello")

		# set continuous nodegraph as backdrop to whole window
		self.graphView = AbstractView(parent=self)
		#self.setCentralWidget(self.graphView)


		#print "initialising status"
		self.status = StatusPane(self, [self.rootPath])
		#self.status.setFocusPolicy(QtCore.Qt.NoFocus)
		#print "status finished"

	def initSignals(self):
		self.status.assetChanged.connect(self.onAssetChanged)
		self.graphView.assetChanged.connect(self.onAssetChanged)
		#print "graphView is {}".format(self.graphView)
		pass

	def onAssetChanged(self, assetInfos):
		"""receives a list of [assetItem]"""
		self._asset = assetInfos[0]
		self.graphView.onAssetChanged(assetInfos)
		self.status.updateCurrentAsset(assetInfos[0])

	# def keyPressEvent(self, event):
	# 	print "event is {}".format(event)
	# 	super(TilePileUI, self).keyPressEvent(event)

	# def focusInEvent(self, event):
	# 	print "main focusIn is {}".format(event.reason())
	#
	# def focusOutEvent(self, event):
	# 	print "main focusOut is {}".format(event.reason())


	def mainDimensions(self):
		#print "QtWidgets frame geo is {}".format(self.frameGeometry())
		sizeRect = self.frameGeometry()
		width = sizeRect.width()
		height = sizeRect.height()
		return width, height

	def closeEvent(self, event):
		"""saves graph to maya maybe"""
		#self.graphView.saveToScene()
		print ""
		print "until we tile again"
		print ""
		event.accept()