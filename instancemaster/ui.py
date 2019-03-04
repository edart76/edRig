# ui for instanceMaster
# left is list of all leaf instances
# right is tree view of instances contained in selected
# get lists, lookup, new instance and master updates working
# then allow splitting of instances from the tree view
from PySide2 import QtGui, QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from edRig.instancemaster.model import SceneInstanceModel

def show():
	eyy = InstanceMasterUI()
	eyyyyy = eyy.show()
	return eyyyyy

class InstanceMasterUI(QtWidgets.QMainWindow):
	"""main TilePile window"""
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

		print "tp init finished"

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

		self.setCentralWidget(self.mainFrame)
		self.setGeometry(200, 200, 700, 700)
		self.setWindowTitle("InstanceMaster v0.0")
		self.width, self.height = self.mainDimensions()

	def mousePressEvent(self, event):
		#self.graph.viewer().mousePressEvent(event)
		pass

	def mainDimensions(self):
		print "QtWidgets frame geo is {}".format(self.frameGeometry())
		sizeRect = self.frameGeometry()
		width = sizeRect.width()
		height = sizeRect.height()
		return width, height

	def getMayaWindow(self):
		pointer = omui.MQtUtil.mainWindow()
		return shiboken2.wrapInstance(long(pointer), QtWidgets.QWidget)

class InstanceCatalogue(QtWidgets.QListWidget):
	def __init__(self, parent=None, sceneModel=None):
		super(InstanceCatalogue, self).__init__(parent)
		self.model = sceneModel
		self.refresh()

	def refresh(self):
		"""updates UI with list of all master instances"""
		self.clear()
		newList = sorted(self.model.listAllMasters().keys())
		for i in newList:
			self.addItem(i)


	pass

class InstanceTreeView(QtWidgets.QTreeWidget):
	def __init__(self, parent=None, sceneModel=None):
		super(InstanceTreeView, self).__init__(parent)
		pass
	pass

class ContextMenu(object):
	pass