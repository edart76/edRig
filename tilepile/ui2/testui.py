
from PySide2 import QtGui, QtWidgets, QtCore
import shiboken2
import maya.OpenMayaUI as omui
from edRig.tilepile.ui2.abstractview import AbstractView
from edRig.tilepile.ui2.statuspane import StatusPane
from edRig.pipeline import TempAsset
from edRig import ROOT_PATH
from edRig.tilepile.ui2.textedit import TextEditWidget, CodeEditor

def show():
	eyy = TestUi()
	eyyyyy = eyy.show()
	return eyyyyy


class TestUi(QtWidgets.QMainWindow):
	"""main TilePile window"""
	def __init__(self):
		super(TestUi, self).__init__()
		self.test = None

		self.text = "hello :)"
		self.width = 0
		self.height = 0

		self.rootPath = ROOT_PATH

		self.initUi()

		self.setWindowModality(QtCore.Qt.WindowModal)



	def initUi(self):
		"""no windows
		no widgets
		only beautiful seamless nodes"""

		parent = self.getMayaWindow()
		parentWindow = QtWidgets.QMainWindow(parent)
		#self.setText("hello")

		# set continuous nodegraph as backdrop to whole window
		#self.test = TextEditWidget(self)
		self.test = CodeEditor(self)
		self.setCentralWidget(self.test)
		#self.status.setFocusPolicy(QtCore.Qt.NoFocus)
		#print "status finished"


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


	def getMayaWindow(self):
		pointer = omui.MQtUtil.mainWindow()
		return shiboken2.wrapInstance(long(pointer), QtWidgets.QWidget)
