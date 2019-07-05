# extra widgets to sit below the graphview
from edRig import attrio
from PySide2 import QtCore, QtGui, QtWidgets


class ExtrasWidget(QtWidgets.QWidget):
	"holds all extra things"
	buildRig = QtCore.Signal(basestring)

	def __init__(self, parent=None, graphView=None):
		super(ExtrasWidget, self).__init__(parent)
		# make this aware of the common rig controller
		if graphView:
			self.graphView = graphView
			self.controller = graphView.controller

		# everything will fit in here
		self.hBox = QtWidgets.QHBoxLayout(self)
		self.steps = StepsWidget(self)
		self.fileIo = FileIoWidget(self)

		self.hBox.addWidget(self.steps)
		self.hBox.addWidget(self.fileIo)
		self.setLayout(self.hBox)

		# signals
		self.steps.stepButtonClicked.connect(self.buildRig)


class StepsWidget(QtWidgets.QWidget):
	"""buttons to build rig to various stages"""
	stepButtonClicked = QtCore.Signal(basestring)

	def __init__(self, parent=None):
		super(StepsWidget, self).__init__(parent)

		self.vBox = QtWidgets.QVBoxLayout(self)
		for i in ["plan", "build", "run"]:
			button = StepButton(self)
			button.setText(i)
			button.stepClicked.connect(self.emitStep)
			self.vBox.addWidget(button)
		self.setLayout(self.vBox)

	def emitStep(self, text):
		print "step {} pressed".format(text)
		self.stepButtonClicked.emit(text)


class StepButton(QtWidgets.QPushButton):
	# i couldn't find a better way for a button to emit its own text
	stepClicked = QtCore.Signal(basestring)

	def __init__(self, parent=None):
		super(StepButton, self).__init__(parent)
		self.setText("blankStep")
		self.clicked.connect(self.emitText)

	def emitText(self):
		text = self.text()
		self.stepClicked.emit(text)


class FileIoWidget(QtWidgets.QWidget):
	openCalled = QtCore.Signal()
	importCalled = QtCore.Signal()
	newTilePileCalled = QtCore.Signal()
	saveCalled = QtCore.Signal()
	saveAsCalled = QtCore.Signal()

	def __init__(self, parent=None):
		super(FileIoWidget, self).__init__(parent)
		self.vBox = QtWidgets.QVBoxLayout(self)
		if parent:
			self.graphView = parent.graphView
			self.tilePileFile = None

		openButton = QtWidgets.QPushButton(self)
		openButton.setText("open")
		importButton = QtWidgets.QPushButton(self)
		importButton.setText("import")
		newButton = QtWidgets.QPushButton(self)
		newButton.setText("new tile pile")
		saveButton = QtWidgets.QPushButton(self)
		saveButton.setText("save")
		saveAsButton = QtWidgets.QPushButton(self)
		saveAsButton.setText("save as")

		for i in [openButton, importButton, newButton,
		          saveButton, saveAsButton]:
			self.vBox.addWidget(i)

		# wire signals
		openButton.clicked.connect(self.openCalled)
		importButton.clicked.connect(self.importCalled)
		newButton.clicked.connect(self.newTilePileCalled)
		saveButton.clicked.connect(self.saveCalled)
		saveAsButton.clicked.connect(self.saveAsCalled)

		self.openCalled.connect(self.openTilePile)
		self.importCalled.connect(self.importTilePile)
		self.saveCalled.connect(self.saveTilePile)
		self.saveAsCalled.connect(self.saveAsTilePile)
		self.newTilePileCalled.connect(self.newTilePile)

		self.setLayout(self.vBox)

	def openTilePile(self):
		tilePileFile = QtWidgets.QFileDialog.getOpenFileName(
			parent=self)[0]
		print "open file is {}".format(tilePileFile)
		if not tilePileFile:
			return
		serialised = attrio.ioinfo(mode="in", path=tilePileFile)
		print "loaded data is {}".format(serialised)
		self.graphView.clear_session()
		self.graphView.controller.clearRig()
		self.graphView.loadGraphFromRig(serialised)
		return serialised
		pass

	def importTilePile(self):
		nopeDialog = QtWidgets.QDialog()
		nopeLabel = QtWidgets.QLabel(nopeDialog)
		nopeLabel.setText("not implemented yet")
		nopeDialog.show()

	def newTilePile(self):
		self.graphView.clear_session()
		self.graphView.controller.clearRig()

	def saveAsTilePile(self, file=None):
		saveData = self.graphView.serialiseGraphAndRig()
		if not file:
			tilePileFile = QtWidgets.QFileDialog.getSaveFileName(
				parent=self)[0]
		else:
			tilePileFile = file

		print "save as file is {}".format(tilePileFile)
		print "save as data is {}".format(saveData)
		if not tilePileFile:
			return

		if not attrio.checkFileExists(tilePileFile):
			attrio.makeBlankFile(path=tilePileFile)
		attrio.ioinfo(name="testPileSaveAs", mode="out",
		              info=saveData, path=tilePileFile)
		self.tilePileFile = tilePileFile

	def saveTilePile(self):
		self.saveAsTilePile(file=self.tilePileFile)


pass
