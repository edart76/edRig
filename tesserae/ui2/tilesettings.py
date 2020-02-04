"""settings widget appended to bottom of tiles
allowing for more granular control"""
from PySide2 import QtCore, QtWidgets, QtGui
from edRig.lib.python import Signal, AbstractTree
from edRig.tesserae.ui2.lib import ContextMenu, expandingPolicy
from edRig.tesserae.expression import EVALUATOR
from edRig.structures import ActionItem

# t i m e _ t o _ h a c k

""" I think I've made a mistake with this in giving the main tree object 
and the treeModel kind of equal priority, updatbing each other - 
however, if I were to assume that the model has priority for the duration,
I would need extra interface infrastructure to interact with it during 
a node's execution

conceptually, if not technically, it is more elegant to me that direct interaction
happen only between pure objects: abstractNode, abstractTree, abstractGraph etc,
and have no 'direct' dependence on a third party
"""

shrinkingPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Minimum,
	QtWidgets.QSizePolicy.Minimum,
)

class TileSettings(QtWidgets.QTreeView):
	"""widget for viewing and editing an AbstractTree
	display values in columns, branches in rows"""
	highlightKind = {
		"error" : QtCore.Qt.red,
		"warning" : QtCore.Qt.yellow,
		"success" : QtCore.Qt.green,
	}

	def __init__(self, parent=None, tree=None):
		""":param tree : AbstractTree"""
		super(TileSettings, self).__init__(parent)
		self.setAnimated(True) # attend first to swag
		self.setAutoExpandDelay(0.1)

		self.setAcceptDrops(True)
		self.setDragDropMode(
			QtWidgets.QAbstractItemView.InternalMove
		)

		self.menu = ContextMenu(self)
		# self.makeMenu()
		# self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		# self.customContextMenuRequested.connect(self.onContextPoint)


		self.highlights = {} # dict of tree addresses to highlight
		self.tree = None
		self.root = None
		self.contentChanged = Signal()
		self.selectedEntry = None
		self.actions = {}
		self.modelObject = None
		if tree:
			tree = self.setTree(tree)

		# appearance
		header = self.header()
		header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		header.setStretchLastSection(False)
		#self.setFirstColumnSpanned(0, self.rootIndex(), True)
		#header.setSectionResizeMode(5, QtWidgets.QHeaderView.Stretch)
		self.setUniformRowHeights(True)
		self.setIndentation(10)
		self.setAlternatingRowColors(True)
		self.showDropIndicator()

		self.initActions()

		header.geometriesChanged.connect( self.resizeToTree )
		self.collapsed.connect( self.resizeToTree )
		self.expanded.connect( self.resizeToTree )


		#self.setSizePolicy( shrinkingPolicy )
		self.setSizePolicy( expandingPolicy )
		self.header().setSizePolicy( expandingPolicy )

	def resizeToTree(self):
		#self.header().resizeToContents()

		width = self.size().width()
		height = 40 * self.header().count()
		self.resize( width, height )
		#self.header().resize( width, height )

		# self.header().resizeSections()
		# self.adjustSize()

		pass

	def makeMenu(self):

		self.menu.clearCustomEntries()
		# actionDict = {"copy" : ActionItem(execDict={ "func" : self.copyEntry}),
		#               "paste" : ActionItem(execDict={ "func" : self.pasteEntry})}
		# self.menu.buildMenusFromDict(actionDict)
		self.menu.add_action(func=self.copyEntry)
		self.menu.add_action(func=self.pasteEntry)


	def test(self):
		print "hey"

	def copyEntry(self):
		print "copying"
		clip = QtGui.QGuiApplication.clipboard()
		indices = self.selectedIndexes() # i hate
		print "indices {}".format(indices)
		""" returns a python list of qModelIndices """
		if not indices:
			print( "no entries selected" )
			return
		index = indices[0] # only copying single entry for now
		# obj = self.modelObject.data( index )
		# print( "obj {}, type {}".format(obj, type(obj)))
		# only unicode string representation
		# need standardItem from model index
		# item = self.modelObject.itemFromIndex( index )
		# print( "item {}".format(item))

		mime = self.modelObject.mimeData( [index] )
		print( "copy mime {}".format(mime.text()))
		clip.setMimeData(mime)

		"""get mime of all selected objects
		set to clipboard
		"""


		pass
	def pasteEntry(self):
		print "pasting"
		indices = self.selectedIndexes() # i strongly hate
		if not indices:
			return
		index = indices[0]
		clip = QtGui.QGuiApplication.clipboard()
		data = clip.mimeData()
		print "mime is {}".format(data.text())
		regenDict = eval(data.text()) # this is probably extremely dangerous lol
		pasteTree = AbstractTree.fromDict(regenDict)

		# get parent item of selected index, addChild with abstract tree,
		# build from tree for items
		commonParentIndex = index.parent()
		commonParentItem = self.modelObject.itemFromIndex( commonParentIndex ) \
		                   or self.modelObject.invisibleRootItem()

		commonParentItem.tree.addChild(pasteTree)
		self.modelObject.buildFromTree(pasteTree, commonParentItem)





		# self.modelObject.beginInsertRows()
		# self.modelObject.beginInsertColumns()
		#
		# # add new tree stuff
		#
		# self.modelObject.endInsertColumns()
		# self.modelObject.endInsertRows()

		""" get selected object or next free index
		deserialise mime data to tree branches
		add tree children
		setTree on the new tree object
		"""
		pass

	# def mousePressEvent(self, *args):
	# 	print "mouse settings"
	# 	#super(TileSettings, self).mousePressEvent(*args)

	def contextMenuEvent(self, event):
		print "settings context event"
		self.onContext( event)

	def onContext(self, event):
		self.makeMenu()
		#pos = event.localPos()
		pos = event.globalPos()
		menu = self.menu.exec_( pos )

	def onContextPoint(self, qPoint):
		self.makeMenu()
		menu = self.menu.exec_( self.viewport().mapToGlobal(qPoint) )
		print "settingsMenu is {}".format(menu)

	# def mousePressEvent(self, event):
	# 	if event.button() == QtCore.Qt.LeftButton:
	# 		super(TileSettings, self).mousePressEvent(event)
	# 		return
	# 	if event.button == QtCore.Qt.RightButton:
	# 		self.makeMenu()
	# 		menu = self.menu.exec_( event.globalPos() )
	# 		print menu



	def showMenu(self, *args, **kwargs):
		return self.menu.exec_(*args, **kwargs)


	def dragEnterEvent(self, event):
		
		super(TileSettings, self).dragEnterEvent(event)
		# event.accept()
		
		
	def dragMoveEvent(self, event):
		
		super(TileSettings, self).dragMoveEvent(event)
		# event.accept()

	def keyPressEvent(self, event):
		
		super(TileSettings, self).keyPressEvent(event)
		pass


	def setTree(self, tree):
		"""associates widget with AbstractTree object"""
		self.tree = tree
		self.root = tree.root
		tree.valueChanged.connect(self.contentChanged)
		tree.structureChanged.connect(self.contentChanged)

		self.modelObject = AbstractTreeModel(tree=self.tree)
		self.setModel(self.modelObject)

		self.resizeToTree()

		return self.modelObject


	def addHighlight(self, address, kind):
		"""adds a highlight to TreeView line, depending on reason"""
		colour = QtCore.QColor(self.highlightKind[kind])
		self.highlights[address] = kind


	def initActions(self):
		"""sets up copy, add, delete etc actions for branch entries"""


class AbstractBranchItem(QtGui.QStandardItem):
	"""small wrapper allowing standardItems to take tree objects directly"""
	ICONS = {}

	def __init__(self, tree, root=None):
		""":param tree : AbstractTree"""
		super(AbstractBranchItem, self).__init__(tree.name)
		self.tree = tree or AbstractTree()
		self.root = None # all have a ref to the root
		self.setColumnCount(1)
		self.trueType = type(self.tree.name)

		self.icon = tree.extras.get("icon")
		if self.icon and self.icon in self.ICONS:
			self.icon = QtGui.QIcon(self.icon)

		# title and value are taken care of by inserting columns
		#self.addValueData()
		
	def setData(self, value, *args, **kwargs): # sets the NAME of the tree
		name = self.tree._setName(value)
		# print "args {}".format(args)
		# print "kwargs {}".format(kwargs)
		"""args and kwargs contain nothing useful, or even related to value"""
		super(AbstractBranchItem, self).setData(name, *args, **kwargs)

	def data(self, role):
		""" just return branch name
		data is used when regenerating abstractTree from model"""
		base = super(AbstractBranchItem, self).data(role)
		#return self.trueType(base)
		return base

	def addValueData(self):
		"""for now this only handles strings
		in future it may be worth handling dicts, lists etc"""
		# textItem = QtCore.QStandardItem(self.tree.value)
		textItem = AbstractValueItem(self.tree)
		#self.appendColumn([textItem])
		self.insertColumn( 1, [textItem])
		#self.setChild(0, 1, textItem)
		pass
		"""although it makes sense conceptually, direct parent/child
		relation between branch and value items cannot be done,
		as they must both appear on same row"""

class AbstractValueItem(QtGui.QStandardItem):
	"""overly specific but it's fine
	differentiate branch tag from actual value"""
	def __init__(self, tree):
		self.tree = tree
		self.trueType = type(self.tree.value)
		# special treatment for illegal types, hacky for now
		# if isinstance(tree, (tuple,)):
		# 	self.tree = str(self.tree)
		value = self.processValue(self.tree.value)

		super(AbstractValueItem, self).__init__(value)

		# if self.tree.value is None:
		# 	self.setText("")

	def processValue(self, value):
		if value is None:
			return ""
		return str(value)

	def setData(self, value, *args, **kwargs):
		"""qt item objects manipulate trees directly, so
		anything already connected to the tree object signals
		works properly"""
		if self.trueType != type(value):
			self.trueType = type(value)
		self.tree.value = self.trueType(value)
		super(AbstractValueItem, self).setData(value, *args, **kwargs)

	def data(self, role):
		base = super(AbstractValueItem, self).data(role)
		return base





class AbstractTreeModel(QtGui.QStandardItemModel):


	def __init__(self, tree, parent=None):
		super(AbstractTreeModel, self).__init__(parent)
		self.tree = None
		self.root = None
		self.setTree(tree)
		self.atRoot = False
		self.setHorizontalHeaderLabels(["branch", "value"])

	# drag and drop support
	def supportedDropActions(self):
		return QtCore.Qt.MoveAction

	def mimeTypes(self):
		""" use built in abstractTree serialisation to reduce
		entries to plain text, then regenerate them after """
		types = ["text/plain"]
		return types

	def mimeData(self, index):
		item = self.itemFromIndex( index[0] )
		tree = item.tree
		text = str(tree.serialise() )
		mime = QtCore.QMimeData()
		mime.setText( text )
		return mime

	def dropMimeData(self, data, action, row, column, parentIndex):
		if action == QtCore.Qt.IgnoreAction:
			return True
		if data.hasText():
			#text = dict( data.text())
			mimeText = data.text()
			print("dropped text is {}".format(mimeText))

			info = eval(mimeText)
			print("eval'd info is {}".format(info))

			tree = AbstractTree.fromDict(info)

			self.beginInsertRows( parentIndex, row, row )
			#pointer = parentIndex.internalPointer() # crashes
			#print( "pointer {}".format(pointer))

			parentItem = self.itemFromIndex( parentIndex )
			if not parentItem:
				parentItem = self.invisibleRootItem()
				parentTree = self.tree.root
			else:
				parentTree = parentItem.tree
			print( "parentItem {}".format(parentItem))

			# rebuild abstract tree from parent downwards,
			# to take account of order
			self.buildFromModel(parentItem, parentTree)

			# print("jhgjh")
			# self.buildFromTree(tree, parentItem)
			#self.setTree(parentTree.root)
			print("jkhkjgk")
			self.endInsertRows()

			# destroy parent tree branches and rebuild from model

			print( "dropped tree value is {}".format( tree.value))

		return True

	def buildFromModel(self, parentItem, parentTree=None):
		"""rebuilds a section of the abstractTree from the ui model
		:param parentItem : parent standardItem below which to rebuild"""

		for i in range(parentItem.rowCount()):
			child = parentItem.child(i)
			print( "model child is {}".format(child))




	def setTree(self, tree):
		self.tree = tree
		self.clear()
		#self.root = AbstractBranchItem(tree.root)
		self.root = self.invisibleRootItem()
		self.root.tree = tree.root
		#self.appendRow(self.root)
		#self.buildFromTree(self.tree, parent=self.root)
		for i in self.tree.root.branches:
			#print "i tree is {}".format(i)
			self.buildFromTree(i, parent=self.root)

			#self.buildFromTree(i, parent=self.root)


			pass

	def buildFromTree(self, tree, parent=None):
		""":param tree : AbstractTree
		:param parent : AbstractBranchItem below which to build"""
		branchItem = AbstractBranchItem(tree=tree, root=self.tree.root)
		textItem = AbstractValueItem(tree)

		parent.appendRow( [branchItem, textItem] )
		#parent.appendRow( branchItem )
		for i in tree.branches:
			self.buildFromTree(i, parent=branchItem)
		return branchItem


