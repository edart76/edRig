# build the tesserae window
from PySide2 import QtGui, QtWidgets, QtCore
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui
#from edRig import omui
from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.ui2.statuspane import StatusPane
from edRig.tesserae.constant import debugEvents
from edRig.tesserae.ui2.lib import  MyDockingUI, dock_window, getMayaWindow
from edRig.pipeline import TempAsset
from edRig import ROOT_PATH
from edRig.tesserae import mainGraph, AbstractGraph

from tree.ui.widget import AllEventEater

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# temp, putting this here until a node solution is found
# saves path on close, loads on open
currentPath = ""

def getMayaWindow():
	ptr = omui.MQtUtil.mainWindow()
	widget = wrapInstance( int( ptr ), QtWidgets.QWidget )
	#widget = wrapInstance( long( ptr ), QtWidgets.QMainWindow )
	return widget

def getMayaObject():
	ptr = omui.MQtUtil.mainWindow()
	widget = wrapInstance( int( ptr ), QtCore.QObject )
	return widget

windows = []




#class TilePileUI(QtWidgets.QWidget):
#class TilePileUI(QtWidgets.QApplication):
#class TilePileUI(MyDockingUI):
class TilePileUI(QtWidgets.QMainWindow):
#class TilePileUI(MayaQWidgetDockableMixin, QtWidgets.QWidget):
#class TilePileUI(MayaQWidgetDockableMixin):
	"""main TilePile window"""
	assetChanged = QtCore.Signal(list)
	CONTROL_NAME = "TilePile"
	DOCK_LABEL_NAME = "TilePile"
	def __init__(self, parent=None, graph=None):
		super(TilePileUI, self).__init__(parent)
		#super(TilePileUI, self).__init__([])
		self.graphView = None # type: AbstractView
		self.graph = graph or AbstractGraph.startup("newGraph")
		self.text = "hello :)"
		self.width = 700
		self.height = 700

		self.rootPath = ROOT_PATH

		self.initUi()
		self.initSignals()
		#self.setWindowModality(QtCore.Qt.WindowModal)
		#self.setWindowFlags(QtCore.Qt.Window)
		self.installEventFilter(AllEventEater(self))
		self.resize(self.width, self.height)

		self.savePath = None
		self.saveFolder = None

		self.hasChanged = False # for checking saves?

		self._asset = None

		print("tp init finished")

	@property
	def asset(self):
		return self._asset or TempAsset


	def initUi(self):
		"""no windows
		no widgets
		only beautiful boundless nodes"""


		# set continuous nodegraph as backdrop to whole window
		self.graphView = AbstractView(parent=self, graph=self.graph)
		if isinstance(self, QtWidgets.QMainWindow):
			self.setCentralWidget(self.graphView)


		self.status = StatusPane(self, [self.rootPath])

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

	def keyPressEvent(self, event):
		print("main keyPress  {}".format(event.key()))
		# this stops events passing back to maya ui
		#super(TilePileUI, self).keyPressEvent(event)
		self.graphView.keyPressEvent(event)

	def mousePressEvent(self, event):
		if debugEvents: print("main mousePress")
		super(TilePileUI, self).mousePressEvent(event)

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

	def show(self, *args, **kwargs):
		""" hook for graph setup"""
		self.graphView.loadFromScene()
		return super(TilePileUI, self).show(*args, **kwargs)

	def closeEvent(self, event):
		"""saves graph to maya maybe"""
		self.graphView.saveToScene()
		print("")
		print("until we tile again")
		print("")
		# remove reference to window
		if self in windows:
			windows.remove(self)
		super(TilePileUI, self).closeEvent(event)


def show():

	mayaWindow = getMayaWindow()
	mayaObj = getMayaObject()

	#win = mayaObj.findChild( TilePileUI )

	win = TilePileUI( mayaWindow )
	#win = TilePileUI( )
	win.graphView.loadFromScene()
	#ref = win.show(dock=False)
	ref = win.show()

	# add jointcurveop for testing
	nodeA = win.graph.addNode("JointCurveOp", name="jc_A")
	nodeB = win.graph.addNode("JointCurveOp", name="jc_B")

	win.graph.addEdge(nodeA.getOutput("joint0"),
	                  nodeB.getInput("parent"))


	windows.append(win)
	return win



