# smaller widgets contained on ui tiles to avoid attribute editors
from PySide2 import QtCore, QtWidgets, QtGui
from edRig.tesserae.ui2.textedit import CodeEditor
import random

# node widgets are ported from nodeGraphQt, but i basically wrote half of them anyway
class _NodeGroupBox(QtWidgets.QGroupBox):
	def __init__(self, label, parent=None):
		super(_NodeGroupBox, self).__init__(parent)
		margin = (0, 0, 0, 0)
		padding_top = '14px'
		if label == '':
			margin = (0, 2, 0, 0)
			padding_top = '2px'
		# style = STYLE_QGROUPBOX.replace('$PADDING_TOP', padding_top)
		self.setMaximumSize(120, 50)
		self.setTitle(label)
		#self.setStyleSheet(style)

		self._layout = QtWidgets.QVBoxLayout(self)
		self._layout.setContentsMargins(*margin)
		self._layout.setSpacing(1)

	def add_node_widget(self, widget):
		self._layout.addWidget(widget)


class NodeBaseWidget(QtWidgets.QGraphicsProxyWidget):
	"""	proxy to embed widgets in noe graphics
	"""
	value_changed = QtCore.Signal(str, object)

	def __init__(self, parent=None, name='widget', label=''):
		super(NodeBaseWidget, self).__init__(parent)
		# self.setZValue(Z_VAL_NODE_WIDGET)
		self._name = name
		self._label = label

	def setWidget(self, widget):
		"""set proper alignment automatically"""
		super(NodeBaseWidget, self).setWidget(widget)
		widget.setAlignment(QtCore.Qt.AlignCenter)
		widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
		                        QtWidgets.QSizePolicy.Ignored)

	def _value_changed(self):
		self.value_changed.emit(self.name, self.value)

	def setToolTip(self, tooltip):
		tooltip = tooltip.replace('\n', '<br/>')
		tooltip = '<b>{}</b><br/>{}'.format(self.name, tooltip)
		super(NodeBaseWidget, self).setToolTip(tooltip)

	# def mousePressEvent(self, event):
	# 	# if self.widget:
	# 	# 	self.widget.mousePressEvent(event)
	# 	super(NodeBaseWidget, self).mousePressEvent(event)
	#
	# def keyPressEvent(self, event):
	# 	#super(NodeBaseWidget, self).keyPressEvent(event)
	# 	print "widg key press"
	# 	if self.widget:
	# 		self.widget.keyPressEvent(event)

	def disable(self):
		"""stops user input on connected inputs"""
		self.widget.setReadOnly(True)

	def enable(self):
		self.widget.setReadOnly(False)

	@property
	def widget(self):
		raise NotImplementedError

	@property
	def value(self):
		raise NotImplementedError

	@value.setter
	def value(self, text):
		raise NotImplementedError

	@property
	def label(self):
		return self._label

	@label.setter
	def label(self, label):
		self._label = label

	@property
	def type(self):
		return str(self.__class__.__name__)

	@property
	def node(self):
		self.parentItem()

	@property
	def name(self):
		return self._name

class NameTagWidget(NodeBaseWidget):
	"""used to display the name of a node and fluidly rename it"""
	def __init__(self, parent=None, initName="newNode", label=""):
		super(NameTagWidget, self).__init__(parent)
		self.line = QtWidgets.QLineEdit()
		self.line.setText(initName)
		self.line.setAlignment(QtCore.Qt.AlignCenter)
		self.line.setSizePolicy(QtWidgets.QSizePolicy.Minimum,
		                        QtWidgets.QSizePolicy.Ignored)
		self.line.updateGeometry()
		#self.line.setReadOnly(False)
		self.line.editingFinished.connect(self._value_changed)
		#group = _NodeGroupBox(label)
		#group.add_node_widget(self.line)
		self.setWidget(self.line)

	# def mousePressEvent(self, event):
	# 	"""highlight text to be renamed"""
	# 	#self.line.setReadOnly(False)
	# 	self.line.setSelection(0, len(self.line.text()))
	# 	super(NameTagWidget, self).mousePressEvent(event)

	def onEditFinished(self):
		"""return to read-only"""
		# self.line.setReadOnly(True)
		self.line.updateGeometry()


	@property
	def widget(self):
		return self.line

	@property
	def value(self):
		return self.line.text()

	@value.setter
	def value(self, val):
		self.setText(val)

class NodeLabel(NodeBaseWidget):
	"""used to put a label on it"""

class NodeComboBox(NodeBaseWidget):
	"""
	ComboBox Node Widget.
	"""

	def __init__(self, parent=None, name='', value=None, label='', items=None):
		super(NodeComboBox, self).__init__(parent, name, label)
		# self.setZValue(Z_VAL_NODE_WIDGET + 1)
		self._combo = QtWidgets.QComboBox()
		# self._combo.setStyleSheet(STYLE_QCOMBOBOX)
		self._combo.setMinimumHeight(24)
		self._combo.activated.connect(self._value_changed)
		list_view = QtWidgets.QListView(self._combo)
		# list_view.setStyleSheet(STYLE_QLISTVIEW)
		self._combo.setView(list_view)
		self._combo.clearFocus()
		group = _NodeGroupBox(label)
		group.add_node_widget(self._combo)

		self.setWidget(group)
		self.add_items(items)
		if value:
			self.value = value

	@property
	def type(self):
		return 'ComboNodeWidget'

	@property
	def widget(self):
		return self._combo

	@property
	def value(self):
		return str(self._combo.currentText())

	@value.setter
	def value(self, text=''):
		index = self._combo.findText(text, QtCore.Qt.MatchExactly)
		self._combo.setCurrentIndex(index)

	def add_item(self, item):
		self._combo.addItem(item)

	def add_items(self, items=None):
		if items:
			self._combo.addItems(items)

	def all_items(self):
		return [self._combo.itemText(i) for i in range(self._combo.count)]

	def sort_items(self):
		items = sorted(self.all_items())
		self._combo.clear()
		self._combo.addItems(items)

	def clear(self):
		self._combo.clear()


class NodeLineEdit(NodeBaseWidget):
	"""
	LineEdit Node Widget.
	"""

	def __init__(self, parent=None, name='', label='', text=''):
		super(NodeLineEdit, self).__init__(parent, name, label)
		self._ledit = QtWidgets.QLineEdit()
		# self._ledit.setStyleSheet(STYLE_QLINEEDIT)
		self._ledit.setAlignment(QtCore.Qt.AlignLeft)
		self._ledit.editingFinished.connect(self._value_changed)
		self._ledit.clearFocus()
		group = _NodeGroupBox(label)
		group.add_node_widget(self._ledit)
		self.setWidget(group)
		self.text = text
		self.value = text

	@property
	def type(self):
		return 'LineEditNodeWidget'

	@property
	def widget(self):
		return self._ledit

	@property
	def value(self):
		return str(self._ledit.text())

	@value.setter
	def value(self, text=''):
		print ""
		print "setting text box value to {}".format(text)
		self._ledit.setText(text)

class NodeTextEdit(NodeBaseWidget):
	"""text edit widget for more involved code callbacks"""

	def __init__(self, parent=None, name="", label="", text=""):
		super(NodeTextEdit, self).__init__(parent, name, label)
		self.textEdit = CodeEditor()
		group = _NodeGroupBox(label)
		group.add_node_widget(self.textEdit)
		self.setWidget(self.textEdit)
		self.value = text

	@property
	def type(self):
		return "TextEditNodeWidget"

	@property
	def widget(self):
		return self.textEdit

	@property
	def value(self):
		return str(self.textEdit.text())
	@value.setter
	def value(self, val):
		self.textEdit.setText(val)


class NodeCheckBox(NodeBaseWidget):
	"""
	CheckBox Node Widget.
	"""

	def __init__(self, parent=None, name='', label='', text='', state=False):
		super(NodeCheckBox, self).__init__(parent, name, label)
		self._cbox = QtWidgets.QCheckBox(text)
		self._cbox.setChecked(state)
		self._cbox.setMinimumWidth(80)
		# self._cbox.setStyleSheet(STYLE_QCHECKBOX)
		font = self._cbox.font()
		font.setPointSize(11)
		self._cbox.setFont(font)
		self._cbox.stateChanged.connect(self._value_changed)
		group = _NodeGroupBox(label)
		group.add_node_widget(self._cbox)
		self.setWidget(group)
		self.text = text
		self.state = state

	@property
	def type(self):
		return 'CheckboxNodeWidget'

	@property
	def widget(self):
		return self._cbox

	@property
	def value(self):
		return self._cbox.isChecked()

	@value.setter
	def value(self, state=False):
		self._cbox.setChecked(state)

class NodeColourBox(NodeBaseWidget):
	"""box to select a specific RGB colour - maybe later RGBA"""
	def __init__(self, parent=None, name="", label="", value=None):
		if not value:
			value = (random.randint(1,255), random.randint(1,255), random.randint(60,255))
		super(NodeColourBox, self).__init__(parent, name, label)
		self.box = self.makeBox(value)
		self._value = None
		self.qValue = None
		self.value = value
		# self.dialog = QtWidgets.QColorDialog(QtGui.QColour(*value), parent=self)
		# self.dialog.setOption(QtWidgets.QColourDialog.NoButtons, True)
		# self.dialog.setOption(QtWidgets.QColourDialog.ShowAlphaChannel, False)

	def mousePressEvent(self, event):
		"""creates colour dialog on mouse click"""
		colour = QtWidgets.QColorDialog.getColor(
			initial = self.qValue,
			options=[QtWidgets.QColorDialog.NoButtons]
		)
		if colour.isValid():
			self.value = colour
		super(NodeColourBox, self).mousePressEvent(event)

	def makeBox(self, value):
		"""creates a small widget of block colour to display current value"""
		box = QtWidgets.QWidget(self)
		box.setAutoFillBackground(True)
		return box

	def setBoxColour(self, val):
		p = self.box.palette()
		p.setColour(self.box.backgroundRole(), QtGui.QColor(val))
		self.box.setPalette(p)

	@property
	def type(self):
		return "pretty colours"

	@property
	def widget(self):
		return self.box

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self, val):
		self._value = val
		self.qValue = QtGui.QColor(*val)
		self.setBoxColour(self.qValue)


class NodeIntSpinbox(NodeBaseWidget):
	"""
	Int spinbox Node Widget.
	"""

	def __init__(self, parent=None, name='', label='', value=1, min=None, max=None):
		super(NodeIntSpinbox, self).__init__(parent, name, label)
		self._field = self.getField()
		self._field.setMinimumWidth(80)
		# self._field.setStyleSheet(STYLE_QCHECKBOX)
		font = self._field.font()
		font.setPointSize(11)
		self._field.setFont(font)
		self._field.valueChanged.connect(self._value_changed)
		group = _NodeGroupBox(label)
		group.add_node_widget(self._field)
		self.setWidget(group)
		self.value = value
		if max:
			self._field.setMaximum(max)
		if min:
			self._field.setMinimum(min)

	def getField(self):
		return QtWidgets.QSpinBox()

	@property
	def type(self):
		return 'IntSpinboxNodeWidget'

	@property
	def widget(self):
		return self._field

	@property
	def value(self):
		return self._field.value()

	@value.setter
	def value(self, val):
		self._field.setValue(val)

class NodeFloatSpinbox(NodeIntSpinbox):
	def __init__(self, parent=None, name='', label='', value=1, min=None, max=None):
		super(NodeFloatSpinbox, self).__init__(parent, name, label, value, min, max)

	def getField(self):
		return QtWidgets.QDoubleSpinBox()

	@property
	def type(self):
		return 'FloatSpinboxNodeWidget'

