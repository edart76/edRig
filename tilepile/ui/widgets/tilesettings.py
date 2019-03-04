from PySide2 import QtCore, QtWidgets, QtGui
from edRig.tilepile.ui.widgets import dataview


class TileSettingsWidget(QtWidgets.QGroupBox):
	"""procedural menu shown whenever tile is selected"""

	dataView = None
	vBox = None
	widgets = []
	tile = None

	def __init__(self, parent=None):
		super(TileSettingsWidget, self).__init__(parent)
		self.setTitle("tileOpSettings")

		testDict = {
			"root": {
				"how": "shall",
				"I": {
					"sing": "that",
					"majesty": "which",
					"angles": 2
				},
				"admire": "let",
				"list": ["dust", "in", "dust"]
			}
		}
		self.dataView = dataview.DataViewWidget(self)
		# self.dataView.refresh(testDict)
		self.dataView.expandAll()
		#self.settingsWidg = QtWidgets.QWidget(self)
		self.settingsWidg = None
		self.dataLayout = QtWidgets.QVBoxLayout(self)
		#self.dataLayout.addWidget(self.settingsWidg, stretch=2)
		self.dataLayout.addWidget(self.dataView, stretch=3)
		# self.dataView = dataview.DictionaryTreeDialog(testDict)
		self.setLayout(self.dataLayout)

		# policy = QtWidgets.QSizePolicy()
		# policy.setVerticalStretch(0)
		# #policy.expandingDirections()
		# self.setSizePolicy(policy)

	def updateDataView(self, op=None):
		self.dataView.setOp(op)

	# if connected to another attribute, override with QTextEdit,
	# displaying connected attr name and tile
	# then below settings, small description of tile op

	def refreshTileSettingsUi(self, tiles=None):
		self.tile = tiles[-1]
		if self.dataView:
			print "updating dataview"
			self.updateDataView(self.tile.opInstance)
			#self.vBox.addWidget(self.dataView)
		return

		self.tile = None
		if self.settingsWidg:
			self.settingsWidg.deleteLater()
		print "widgets before clear are {}".format(self.widgets)
		if self.widgets:
			for i in self.widgets:
				self.vBox.removeWidget(i)
				i.deleteLater()

		self.vBox = None
		if self.vBox:
			self.vBox.invalidate()
			self.vBox.deleteLater()

		self.settingsWidg = QtWidgets.QWidget(self)
		#self.vBox = QtWidgets.QVBoxLayout(self)

		# called whenever selected node changes
		# passed a list of all selected tiles, just in case
		# for now just the last is enough
		print ""
		print "passed tiles to ui are {}".format(tiles)
		# self.tile = tiles[-1]
		print "tileOpName is {}".format(self.tile.opInstance.opName)
		self.vBox = QtWidgets.QVBoxLayout(self.settingsWidg)
		self.widgets = []
		# #works
		print "widgets during clear are {}".format(
			self.vBox.count())

		for i in self.tile.opInstance.inputs.keys():
			print "found input {}".format(i)
			attrWidget = AttributeItem(
				parent=self, attrDict=self.tile.opInstance.inputs[i], key=i)
			self.widgets.append(attrWidget)
			self.vBox.addWidget(attrWidget)
			attrWidget.adjustSize()
			attrWidget.attrUpdated.connect(self.propagateValue)
			self.vBox.update()

		print "widgets after clear are {}".format(self.widgets)


		self.vBox.update()
		self.settingsWidg.setLayout(self.vBox)
		self.vBox.update()
		self.settingsWidg.update()
		self.dataLayout.addWidget(self.settingsWidg)
		# don't touch it don't touch it it works don't touch it fuck off don't touch it

	def propagateValue(self, attrName, attrValue):
		# takes string name and unit list of whatever value
		print "propagating value"
		attrValue = attrValue[0]
		print "passed name {} attrValue is {}".format(attrName, attrValue)
		self.tile.opInstance.inputs[attrName]["value"] = attrValue

class AttributeItem(QtWidgets.QWidget):
	# procedural widget housing
	attrName = None
	attrType = None
	attrValue = None
	nodeDict = None
	elementWidget = None
	uiUpdated = QtCore.Signal()
	attrUpdated = QtCore.Signal(str, list)

	def __init__(self, parent=None, attrDict=None, key=None):
		super(AttributeItem, self).__init__(parent)

		self.attrDict = attrDict
		print "attrDict is {}".format(self.attrDict)
		self.attrName = key
		#print "attrName is {}".format(self.attrName)
		self.attrType = self.attrDict["datatype"]
		#print "attrType is {}".format(self.attrType)

		self.attrValue = self.attrDict["value"]
		#print "attrValue is {}".format(self.attrValue)
		print ""
		# at assignation check if connected, then retrieve from knob
		# or check tile's own memory

		if self.attrType in typeDict.keys():
			element = typeDict[self.attrType]
		else:
			# null
			return
		self.elementWidget = element(parent=self, attrDict=self.attrDict)

		# signals
		self.elementWidget.valueUpdated.connect(self.uiUpdated)
		self.elementWidget.valueUpdated.connect(self.propagateUiInfo)

		attrLabel = QtWidgets.QLabel(self)
		attrLabel.setText(self.attrName)
		# hBox = the GOAT fight me
		hBox = QtWidgets.QHBoxLayout()
		hBox.addWidget(attrLabel)
		hBox.addWidget(self.elementWidget)
		self.setLayout(hBox)

	def propagateUiInfo(self):
		#self.attrValue = self.elementWidget.outValue
		print "propagating ui info"
		self.attrValue = self.elementWidget.outValue
		self.attrUpdated.emit(self.attrName, [self.attrValue])


#### eventually shift all these widgets on to nodes themselves

class BaseAttributeElement(QtWidgets.QWidget):
	valueUpdated = QtCore.Signal()
	userInput = None

	def __init__(self, parent=None, attrDict=None):
		super(BaseAttributeElement, self).__init__(parent)
		self.attrDict = attrDict
		self.userInput = self.makeUserInput()
		self.setFixedSize(self.size())
		pass

	def onValueUpdated(self):
		print "baseAttrElement value updated"
		self.valueUpdated.emit()

	def setInitValue(self):
		# get current value from nodeDict and set it by default
		initVal = self.attrDict["value"]
		print "initVal is {}".format(initVal)
		if initVal:
			self.userInput.setValue(initVal)

	def setLimits(self):
		# limits
		if "max" in self.attrDict.keys():
			self.userInput.setMaximum(attrDict["max"])
		if "min" in self.attrDict.keys():
			self.userInput.setMinimum(attrDict["min"])

	@property
	def outValue(self):
		print "returning outValue"
		return self.userInput.value()  # see below for use

	def makeUserInput(self):
		pass

	def mousePressEvent(self, event):
		alt_modifier = event.modifiers() == QtCore.Qt.AltModifier
		shift_modifier = event.modifiers() == QtCore.Qt.ShiftModifier
		if event.button() == QtCore.Qt.LeftButton:
			self.LMB_state = True
		elif event.button() == QtCore.Qt.RightButton:
			self.RMB_state = True
		elif event.button() == QtCore.Qt.MiddleButton:
			self.MMB_state = True
		self._origin_pos = event.pos()

	def mouseReleaseEvent(self, event):
		if event.button() == QtCore.Qt.LeftButton:
			self.LMB_state = False
		elif event.button() == QtCore.Qt.RightButton:
			self.RMB_state = False
		elif event.button() == QtCore.Qt.MiddleButton:
			self.MMB_state = False


# yes, every single attribute type needs a special-case widget
# could pass class type procedurally, but typing this is fine
class IntAttributeElement(BaseAttributeElement):
	# signal attrChanged(need uniform signal name)
	# can we just do this?
	# attrChangedSignal = QtWidgets.QSlider.valueChanged

	# this was originally a slider, but then I realised sliders
	# aren't all that useful or efficient space-wise

	def __init__(self, parent=None, attrDict=None):
		# attrDict is child dict of nodeDict[key]
		super(IntAttributeElement, self).__init__(parent, attrDict)

		self.setInitValue()
		self.setLimits()

		self.userInput.valueChanged.connect(self.onValueUpdated)

	def makeUserInput(self):
		widget = QtWidgets.QSpinBox(self)
		return widget

	def mouseMoveEvent(self, event):
		if self.MMB_state:
			pos_x = (event.x() - self._previous_pos.x())
			pos_y = (event.y() - self._previous_pos.y())
			self.userInput.stepBy(pos_y)


class FloatAttributeElement(IntAttributeElement):
	# same as above but accounting for fact Qt doesn't have float sliders
	# is this a fucking win for mel over Qt?
	# big if true

	# create range by placing current value in middle of slider

	def __init__(self, parent=None, attrDict=None):
		super(FloatAttributeElement, self).__init__(parent, attrDict)
		# maybe these object-oriented kids are on to something

	def makeUserInput(self):
		widget = QtWidgets.QDoubleSpinBox(self)
		return widget


class BoolAttributeElement(BaseAttributeElement):
	# on or off. not looking for a lecture, it's one or the other
	def __init__(self, parent=None, attrDict=None):
		super(BoolAttributeElement, self).__init__(parent, attrDict)
		self.userInput.toggled.connect(self.onValueUpdated)

	def makeUserInput(self):
		widget = QtWidgets.QRadioButton(self)
		return widget

	def setInitValue(self):
		initVal = self.attrDict["value"]
		if int(initVal) == 1:
			self.userInput.setChecked()

	@property
	def outValue(self):
		print "bool val is {}".format((1 if self.userInput.isDown() else 0))
		return 1 if self.userInput.isDown() else 0


class EnumAttributeElement(BaseAttributeElement):
	# is it a red brexit, a white brexit, or a blue brexit
	def __init__(self, parent=None, attrDict=None):
		super(EnumAttributeElement, self).__init__(parent, attrDict)
		self.userInput.currentIndexChanged.connect(self.onValueUpdated)

	def makeUserInput(self):
		widget = QtWidgets.QComboBox(self)
		for i in self.attrDict["options"]:
			widget.insertItem(0, i)
		return widget

	@property
	def outValue(self):
		print "enumText is {}".format(self.userInput.currentText())
		print "enumVal is {}".format(self.userInput.currentIndex())
		#return self.userInput.currentIndex()
		return self.userInput.currentText()


class StringAttributeElement(BaseAttributeElement):
	# is it a red brexit, a white brexit, or a blue brexit
	def __init__(self, parent=None, attrDict=None):
		super(StringAttributeElement, self).__init__(parent, attrDict)
		self.userInput.textEdited.connect(self.valueUpdated)

	def makeUserInput(self):
		widget = QtWidgets.QLineEdit(self)
		return widget

	def setInitValue(self):
		initVal = self.attrDict["value"]
		self.userInput.setText(value)


class DimensionalElement(BaseAttributeElement):
	def __init__(self, parent=None, attrDict=None):
		super(DimensionalElement, self).__init__(parent, attrDict)

	def makeUserInput(self):
		widget = QtWidgets.QLabel(self)
		widget.setWordWrap(True)
		widget.setText("this input expects a dimensional input from the graph")
		return widget

	def setInitValue(self):
		pass

	def setLimits(self):
		pass


typeDict = {
	"int": IntAttributeElement,
	"float": FloatAttributeElement,
	"string": StringAttributeElement,
	"enum": EnumAttributeElement,
	"bool": BoolAttributeElement,
	"point": DimensionalElement,
	"curve": DimensionalElement,
	"surface": DimensionalElement,
	"volume": DimensionalElement,
	"0D": DimensionalElement,
	"1D": DimensionalElement,
	"2D": DimensionalElement,
	"3D": DimensionalElement,
	"nD": DimensionalElement
}
