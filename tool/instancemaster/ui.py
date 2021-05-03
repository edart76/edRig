"""ui for InstanceMaster"""

from PySide2 import QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from edRig.tool.instancemaster.model import SceneInstanceModel
from edRig.tesserae.ui2.lib import ContextMenu
from edRig.structures import ActionItem

def show():
	#eyy = dock_window(InstanceMasterUI)
	eyy = InstanceMasterUI()
	eyyyyy = eyy.show()
	return eyyyyy
	#return eyy

class InstanceMasterUI(QtWidgets.QMainWindow):
	"""main TilePile window"""
	onNewMaster = QtCore.Signal()
	def __init__(self):
		super(InstanceMasterUI, self).__init__()
		self.text = "hello :)"
		self.width = 0
		self.height = 0
		self.sceneModel = SceneInstanceModel(ui=self)

		self.initUi()


		self.widgets = []
		# anti rubbish collection

		self.setWindowModality(QtCore.Qt.WindowModal)
		#self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
		                   QtWidgets.QSizePolicy.Expanding)


		self.wireSignals()

		print "IM init finished"

	def initUi(self):
		parent = self.getMayaWindow()
		parentWindow = QtWidgets.QMainWindow(parent)
		self.text = "hello"

		self.mainFrame = QtWidgets.QFrame(self)
		self.mainFrame.setStyleSheet(
			"background-color: rgba(0,0,50,255);"
		)

		self.mainBox = QtWidgets.QHBoxLayout(self)
		self.catalogue = InstanceCatalogue(self, sceneModel=self.sceneModel)
		self.tree = InstanceTreeView(self, sceneModel=self.sceneModel)
		self.mainBox.addWidget(self.catalogue)
		self.mainBox.addWidget(self.tree)
		self.mainFrame.setLayout(self.mainBox)
		self.mainFrame.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
		                   QtWidgets.QSizePolicy.Expanding)

		self.setCentralWidget(self.mainFrame)
		self.setGeometry(200, 200, 700, 700)
		self.setWindowTitle("InstanceMaster v0.0")
		self.width, self.height = self.mainDimensions()

	def sync(self):
		self.catalogue.sync()
		self.tree.sync()

	def mainDimensions(self):
		print "QtWidgets frame geo is {}".format(self.frameGeometry())
		sizeRect = self.frameGeometry()
		width = sizeRect.width()
		height = sizeRect.height()
		return width, height

	def wireSignals(self):
		self.catalogue.onNewMaster.connect(self.newMasterCalled)

	def newMasterCalled(self):
		self.onNewMaster.emit()

	def getMayaWindow(self):
		pointer = omui.MQtUtil.mainWindow()
		return shiboken2.wrapInstance(long(pointer), QtWidgets.QWidget)

class InstanceCatalogue(QtWidgets.QListWidget):
	"""flat list of all master instances"""
	onNewMaster = QtCore.Signal()
	def __init__(self, parent=None, sceneModel=None):
		super(InstanceCatalogue, self).__init__(parent)
		self.model = sceneModel
		#self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
		                   QtWidgets.QSizePolicy.Expanding)

		self.sync()
		self.contextMenu = ContextMenu(self)

	def sync(self):
		"""updates UI with list of all master instances"""
		self.clear()
		newList = sorted(self.model.listAllMasters().keys())
		for i in newList:
			self.addItem(i)

	def buildContext(self):
		self.contextMenu.clearCustomEntries()
		menuDict = {"make new master" : ActionItem({"func" : self.newMasterRequested},
		                                           name="make new master")}
		self.contextMenu.buildMenusFromDict(menuDict)

	def newMasterRequested(self):
		self.onNewMaster.emit()

	def contextMenuEvent(self, event):
		self.buildContext()
		self.contextMenu.exec_(event.globalPos())
		super(InstanceCatalogue, self).contextMenuEvent(event)
		
	def mousePressEvent(self, event):
		self.sync()
		super(InstanceCatalogue, self).mousePressEvent(event)


class InstanceTreeView(QtWidgets.QTreeWidget):
	def __init__(self, parent=None, sceneModel=None):
		super(InstanceTreeView, self).__init__(parent)
		#self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)

	def sync(self):
		pass
	pass
