"""settings widget appended to bottom of tiles
allowing for more granular control"""
from PySide2 import QtCore, QtWidgets, QtGui
from edRig.lib.python import Signal, AbstractTree
from edRig.tesserae.expression import EVALUATOR

# t i m e _ t o _ h a c k


class TileSettings(QtWidgets.QTreeView):
	"""widget for viewing and editing an AbstractTree"""
	highlightKind = {
		"error" : QtCore.Qt.red,
		"warning" : QtCore.Qt.yellow,
		"success" : QtCore.Qt.green,
	}

	def __init__(self, parent=None, tree=None):
		""":param tree : AbstractTree"""
		super(TileSettings, self).__init__(parent)
		self.setAnimated(True) # attend first to swag
		self.setAutoExpandDelay(0.5)

		self.highlights = {} # dict of tree addresses to highlight
		self.tree = None
		self.root = None
		self.contentChanged = Signal()
		self.selectedEntry = None
		self.actions = {}
		self.modelObject = None
		if tree:
			self.setTree(tree)

		self.initActions()

	def setTree(self, tree):
		"""associates widget with AbstractTree object"""
		self.tree = tree
		self.root = tree.root
		tree.valueChanged.connect(self.contentChanged)
		tree.structureChanged.connect(self.contentChanged)

		self.modelObject = AbstractTreeModel(tree=self.tree)
		self.setModel(self.modelObject)


	def addHighlight(self, address, kind):
		"""adds a highlight to TreeView line, depending on reason"""
		colour = QtCore.QColor(self.highlightKind[kind])
		self.highlights[address] = kind

	def initActions(self):
		"""sets up copy, add, delete etc actions for branch entries"""

	# @staticmethod
	# def clearQTreeWidget(treeWidget):
	# 	iterator = QtWidgets.QTreeWidgetItemIterator(treeWidget, QtWidgets.QTreeWidgetItemIterator.All)
	# 	while iterator.value():
	# 		iterator.value().takeChildren()
	# 		iterator += 1
	# 	i = treeWidget.topLevelItemCount() + 1
	# 	if i == 0:
	# 		return
	# 	# print "original topLevelItemCount is {}".format(treeWidget.topLevelItemCount())
	# 	while i >= 0:
	# 		treeWidget.takeTopLevelItem(i)
	# 		# print "topLevelItemCount is {}".format(treeWidget.topLevelItemCount())
	# 		i = i - 1


class AbstractBranchItem(QtGui.QStandardItem):
	"""small wrapper allowing standardItems to take tree objects directly"""
	ICONS = {}

	def __init__(self, tree):
		""":param tree : AbstractTree"""
		super(AbstractBranchItem, self).__init__(tree.name)
		self.tree = tree or AbstractTree()
		self.icon = tree.extras.get("icon")
		if self.icon and self.icon in self.ICONS:
			self.icon = QtGui.QIcon(self.icon)

		# title and value are taken care of by inserting columns
		self.addValueData()
		
	def setData(self, value, *args, **kwargs): # sets the NAME of the tree
		name = self.tree.setName(value)
		# print "args {}".format(args)
		# print "kwargs {}".format(kwargs)
		"""args and kwargs contain nothing useful, or even related to value"""
		super(AbstractBranchItem, self).setData(name, *args, **kwargs)

	def addValueData(self):
		"""for now this only handles strings
		in future it may be worth handling dicts, lists etc"""
		# textItem = QtCore.QStandardItem(self.tree.value)
		textItem = AbstractValueItem(self.tree)
		self.appendColumn([textItem])
		"""currently column only shows up below main heading
		need to fix it"""

class AbstractValueItem(QtGui.QStandardItem):
	"""overly specific but it's fine"""
	def __init__(self, tree):
		self.tree = tree
		self.trueType = type(self.tree.value)
		# special treatment for illegal types, hacky for now
		# if isinstance(tree, (tuple,)):
		# 	self.tree = str(self.tree)
		super(AbstractValueItem, self).__init__(str(tree.value))
	def setData(self, value, *args, **kwargs):
		"""qt item objects manipulate trees directly, so
		anything already connected to the tree object signals
		works properly"""
		self.tree.value = self.trueType(value)
		super(AbstractValueItem, self).setData(value, *args, **kwargs)


class AbstractTreeModel(QtGui.QStandardItemModel):
	"""is this worth it? maybe"""

	def __init__(self, tree, parent=None):
		super(AbstractTreeModel, self).__init__(parent)
		self.tree = None
		self.root = None
		self.setTree(tree)

	def setTree(self, tree):
		self.tree = tree
		self.clear()
		self.root = AbstractBranchItem(tree.root)
		self.appendRow(self.root)
		#self.buildFromTree(self.tree, parent=self.root)
		for i in self.tree.root.branches:
			print "i tree is {}".format(i)
			# self.buildFromTree(i, parent=self.invisibleRootItem())
			self.buildFromTree(i, parent=self.root)
			pass

	def buildFromTree(self, tree, parent=None):
		""":param tree : AbstractTree"""
		item = AbstractBranchItem(tree=tree)
		parent.appendRow(item)
		for i in tree.branches:
			self.buildFromTree(i, parent=item)




	# def _buildBranches(self, tree, parent=None):

#
# class DataViewWidget(QtWidgets.QTreeWidget):
# 	"""widget for viewing an op's data dict
# 	THIS DOES NOT INTERACT WITH THE FILE SYSTEM
# 	the op affects the file, this affects the op"""
#
# 	# ADD CAPABILITY TO ADD AND REMOVE ENTRIES
#
# 	contentChanged = QtCore.Signal()
# 	resizeWidget = QtCore.Signal()
# 	op = None
# 	opData = {}
#
# 	def __init__(self, parent=None):
# 		super(DataViewWidget, self).__init__(parent)
# 		self.setAnimated(True)  # swag
# 		self.setAutoExpandDelay(1)
#
# 		self.itemChanged.connect(self.contentChanged)
#
# 		self.saveButton = QtWidgets.QPushButton(self)
# 		self.saveButton.setText("save")
# 		self.saveButton.clicked.connect(self.updateOpData)
#
# 	def currentDataAsDict(self):
# 		print "currentDataAsDict"
# 		# top = self.topLevelItem(0)
# 		top = self.invisibleRootItem()
# 		# print "top is {}".format(top)
# 		# if not top:
# 		# return None
# 		d = {}
# 		d.clear()
# 		# d = self.toDict(parent=top)
# 		self.toDict(parent=top, targetDict=d)
# 		print "toDict result is {}".format(d)
# 		return d
#
# 	def flags(self, index):
# 		"""everything is editable"""
# 		return (QtCore.Qt.ItemIsEnabled |
# 		        QtCore.Qt.ItemIsSelectable |
# 		        QtCore.Qt.ItemIsEditable)
#
# 	def updateOpData(self):
# 		print "updateOpData"
# 		# print "currentOpData is {}".format(self.op.data)
# 		currentDict = self.currentDataAsDict()
# 		# print "currentDict is {}".format(currentDict)
# 		# self.opData = currentDict
# 		self.op.data.clear()
# 		# self.op.data = currentDict
# 		self.op.data.update(currentDict)
# 		currentDict.clear()
# 		print "new opData is {}".format(self.op.data)
# 		self.clearQTreeWidget(self)
#
# 	def setOp(self, op=None):
# 		print ""
# 		# print "setting op"
# 		# print "passed op is {}".format(op)
# 		self.opData.clear()
# 		if isinstance(op, list):
# 			op = op[-1]
# 		print "op is {}".format(op)
#
# 		self.op = None
# 		self.clearQTreeWidget(self)
# 		# print "current dataview is {}".format(self.currentDataAsDict())
#
# 		self.op = op
# 		self.refresh(self.op.data)
# 		# print "current dataview is {}".format(self.currentDataAsDict())
#
# 	def refresh(self, value={"blank": "dict"}):
# 		print "refreshing"
# 		self.clearQTreeWidget(self)
# 		self.fill_item(self.invisibleRootItem(), value)
# 		self.expandAll()
#
# 	def toDict(self, targetDict={}, parent=None):
# 		# this bit's all mine, and i'm very proud of it
# 		# d = OrderedDict()
# 		# print ""
# 		if not parent:
# 			parent = self.invisibleRootItem()
# 		d = {}
# 		d.clear()
# 		if parent.childCount():
#
# 			if parent.data(0, 0):
# 				d[parent.data(0, 0)] = {}
# 				childDict = d[parent.data(0, 0)]
# 			else:
# 				childDict = d
# 			# d[parent.data(0,0)] = {}
# 			valList = []
#
# 			for i in range(parent.childCount()):
# 				child = parent.child(i)
# 				childData = child.data(0, 0)
# 				print "child data is {}".format(child.data(0, 0))
# 				if child.childCount():
# 					# self.toDict(targetDict=d[parent.data(0,0)], parent=child)
# 					self.toDict(targetDict=childDict, parent=child)
# 				elif isinstance(childData, list):
# 					for i in childData:
# 						self.toDict(targetDict=childDict, parent=child)
# 				else:
# 					valList.append(child.data(0, 0))
# 					if len(valList) == 1:
# 						valList = valList[0]
# 					d[parent.data(0, 0)] = valList
# 					# childDict = valList
#
# 		# if isinstance(targetDict, dict):
# 		targetDict.update(d)
# 		return targetDict
#
# 	def fill_item(self, item, value):
# 		def new_item(parent, text, val=None):
# 			child = QtWidgets.QTreeWidgetItem([text])
# 			child.setFlags((QtCore.Qt.ItemIsEnabled |
# 			                QtCore.Qt.ItemIsSelectable |
# 			                QtCore.Qt.ItemIsEditable))
# 			self.fill_item(child, val)
# 			parent.addChild(child)
# 			child.setExpanded(True)
#
# 		if value is None:
# 			return
# 		elif isinstance(value, dict):
# 			for key, val in sorted(value.items()):
# 				new_item(item, str(key), val)
# 		elif isinstance(value, (list, tuple)):
# 			for i, val in enumerate(value):
# 				new_item(item, str(i), val=val)
# 		# for val in value:
# 		#     text = (str(val) if not isinstance(val, (dict, list, tuple))
# 		#             else '[%s]' % type(val).__name__)
# 		#     new_item(item, text, val=None)
# 		else:
# 			new_item(item, str(value))
#
# 	def clearQTreeWidget(self, treeWidget):
# 		iterator = QtWidgets.QTreeWidgetItemIterator(treeWidget, QtWidgets.QTreeWidgetItemIterator.All)
# 		while iterator.value():
# 			iterator.value().takeChildren()
# 			iterator += 1
# 		i = treeWidget.topLevelItemCount() + 1
# 		if i == 0:
# 			return
# 		# print "original topLevelItemCount is {}".format(treeWidget.topLevelItemCount())
# 		while i >= 0:
# 			treeWidget.takeTopLevelItem(i)
# 			# print "topLevelItemCount is {}".format(treeWidget.topLevelItemCount())
# 			i = i - 1



# class TileSettingsWidget(QtWidgets.QGroupBox):
# 	"""procedural menu shown whenever tile is selected"""
#
# 	dataView = None
# 	vBox = None
# 	widgets = []
# 	tile = None
#
# 	def __init__(self, parent=None):
# 		super(TileSettingsWidget, self).__init__(parent)
# 		self.setTitle("tileOpSettings")
#
# 		testDict = {
# 			"root": {
# 				"how": "shall",
# 				"I": {
# 					"sing": "that",
# 					"majesty": "which",
# 					"angles": 2
# 				},
# 				"admire": "let",
# 				"list": ["dust", "in", "dust"]
# 			}
# 		}
# 		self.dataView = dataview.DataViewWidget(self)
# 		# self.dataView.refresh(testDict)
# 		self.dataView.expandAll()
# 		#self.settingsWidg = QtWidgets.QWidget(self)
# 		self.settingsWidg = None
# 		self.dataLayout = QtWidgets.QVBoxLayout(self)
# 		#self.dataLayout.addWidget(self.settingsWidg, stretch=2)
# 		self.dataLayout.addWidget(self.dataView, stretch=3)
# 		# self.dataView = dataview.DictionaryTreeDialog(testDict)
# 		self.setLayout(self.dataLayout)
#
# 		# policy = QtWidgets.QSizePolicy()
# 		# policy.setVerticalStretch(0)
# 		# #policy.expandingDirections()
# 		# self.setSizePolicy(policy)
#
# 	def updateDataView(self, op=None):
# 		self.dataView.setOp(op)
#
# 	# if connected to another attribute, override with QTextEdit,
# 	# displaying connected attr name and tile
# 	# then below settings, small description of tile op
#
# 	def refreshTileSettingsUi(self, tiles=None):
# 		self.tile = tiles[-1]
# 		if self.dataView:
# 			print "updating dataview"
# 			self.updateDataView(self.tile.opInstance)
# 			#self.vBox.addWidget(self.dataView)
# 		return
#
# 		self.tile = None
# 		if self.settingsWidg:
# 			self.settingsWidg.deleteLater()
# 		print "widgets before clear are {}".format(self.widgets)
# 		if self.widgets:
# 			for i in self.widgets:
# 				self.vBox.removeWidget(i)
# 				i.deleteLater()
#
# 		self.vBox = None
# 		if self.vBox:
# 			self.vBox.invalidate()
# 			self.vBox.deleteLater()
#
# 		self.settingsWidg = QtWidgets.QWidget(self)
# 		#self.vBox = QtWidgets.QVBoxLayout(self)
#
# 		# called whenever selected node changes
# 		# passed a list of all selected tiles, just in case
# 		# for now just the last is enough
# 		print ""
# 		print "passed tiles to ui are {}".format(tiles)
# 		# self.tile = tiles[-1]
# 		print "tileOpName is {}".format(self.tile.opInstance.opName)
# 		self.vBox = QtWidgets.QVBoxLayout(self.settingsWidg)
# 		self.widgets = []
# 		# #works
# 		print "widgets during clear are {}".format(
# 			self.vBox.count())
#
# 		for i in self.tile.opInstance.inputs.keys():
# 			print "found input {}".format(i)
# 			attrWidget = AttributeItem(
# 				parent=self, attrDict=self.tile.opInstance.inputs[i], key=i)
# 			self.widgets.append(attrWidget)
# 			self.vBox.addWidget(attrWidget)
# 			attrWidget.adjustSize()
# 			attrWidget.attrUpdated.connect(self.propagateValue)
# 			self.vBox.update()
#
# 		print "widgets after clear are {}".format(self.widgets)
#
#
# 		self.vBox.update()
# 		self.settingsWidg.setLayout(self.vBox)
# 		self.vBox.update()
# 		self.settingsWidg.update()
# 		self.dataLayout.addWidget(self.settingsWidg)
# 		# don't touch it don't touch it it works don't touch it fuck off don't touch it
#
# 	def propagateValue(self, attrName, attrValue):
# 		# takes string name and unit list of whatever value
# 		print "propagating value"
# 		attrValue = attrValue[0]
# 		print "passed name {} attrValue is {}".format(attrName, attrValue)
# 		self.tile.opInstance.inputs[attrName]["value"] = attrValue
