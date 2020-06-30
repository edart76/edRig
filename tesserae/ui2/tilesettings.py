"""settings widget appended to bottom of tiles
allowing for more granular control"""
# import sys
#
# ps2Path = "C:\Program Files\Autodesk\Maya2018\Python\Lib\site-packages\PySide2"
# ps2Path = "C:\Program Files\Autodesk\Maya2018\Python\Lib\site-packages"
# #ps2Path = ps2Path.replace("\\", "/")
# print(sys.path)
# sys.path.append(ps2Path)
# print(sys.path)


from PySide2 import QtCore, QtWidgets, QtGui
from edRig.lib.python import Signal, AbstractTree
from edRig.tesserae.ui2.lib import ContextMenu, expandingPolicy, getMayaMainWindow, getMayaWindow, \
	BaseMayaUi
from edRig.tesserae.expression import EVALUATOR
from edRig.structures import ActionItem

# t i m e _ t o _ h a c k

""" I think I've made a mistake with this in giving the main tree object 
and the treeModel kind of equal priority, updating each other - 
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

# custom qt data roles
objRole = QtCore.Qt.UserRole + 1


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
		#self.setAnimated(True) # attend first to swag
		#self.setAutoExpandDelay(0.01)

		self.setDragEnabled(True)
		self.setAcceptDrops(True)
		self.setDragDropMode(
			QtWidgets.QAbstractItemView.InternalMove
		)
		self.setSelectionMode( self.ExtendedSelection )
		self.setAutoScroll(False)
		self.setFocusPolicy(QtCore.Qt.ClickFocus)
		self.setEditTriggers(QtWidgets.QTreeView.DoubleClicked |
		                     QtWidgets.QTreeView.EditKeyPressed)

		self.menu = ContextMenu(self)
		# self.makeMenu()
		# self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		# self.customContextMenuRequested.connect(self.onContextPoint)
		self.sizeChanged = Signal()


		self.highlights = {} # dict of tree addresses to highlight
		self.tree = None
		self.root = None
		self.contentChanged = Signal()
		self.selectedEntry = None
		self.actions = {}
		self.modelObject = None


		# appearance
		header = self.header()
		header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
		header.setStretchLastSection(False)

		self.setUniformRowHeights(True)
		self.setIndentation(10)
		self.setAlternatingRowColors(True)
		self.showDropIndicator()

		#self.setSizeAdjustPolicy( QtWidgets.QAbstractScrollArea.AdjustToContents)

		self.initActions()

		# header.geometriesChanged.connect( self.resizeToTree )
		# self.collapsed.connect( self.resizeToTree )
		# self.expanded.connect( self.resizeToTree )

		if tree:
			tree = self.setTree(tree)

		self.savedExpandedTrees = []
		self.savedSelectedTrees = []

		#self.setSizePolicy(expandingPolicy)

	def resizeToTree(self):
		# get rough idea of how long max tree entry is
		maxLen = 0
		for k, v in self.tree.iterBranches():
			maxLen = max(maxLen, len(k) + len(str(v.value)))
		width = maxLen*7 + 30

		#height = self.viewportSizeHint().height()
		count = len( self.tree.root.allBranches( includeSelf=True) )
		if count == 1:
			height = 1
			width = 1
		else:
			height = 20 * count
		index = self.rootIndex()
		#height = ( self.rowHeight( index ) + 2 ) * count
		self.resize( width, height )
		self.sizeChanged()

		pass

	# def sizeHint(self):
	# 	""" minimum size has to encompass all visible branches """




	def makeMenu(self):

		self.menu.clearCustomEntries()
		# actionDict = {"copy" : ActionItem(execDict={ "func" : self.copyEntry}),
		#               "paste" : ActionItem(execDict={ "func" : self.pasteEntry})}
		# self.menu.buildMenusFromDict(actionDict)
		self.menu.add_action(func=self.copyEntry)
		self.menu.add_action(func=self.pasteEntry)
		self.menu.add_action(func=self.display)

	def display(self):
		print(self.tree.display())

	def moveCursor(self, action, modifiers):
		index = self.currentIndex()
		columns = self.model().columnCount(index)
		rows = self.model().rowCount(index.parent())
		if action == self.MoveNext:
			if index.column() + 1 < columns:
				return index.sibling(index.row(), index.column() + 1)
			elif index.row() + 1 < rows:
				return self.model()

		return super(TileSettings, self).moveCursor(action, modifiers)


	def copyEntry(self):
		#print "copying"
		clip = QtGui.QGuiApplication.clipboard()
		indices = self.selectedIndexes() # i hate
		#print "indices {}".format(indices)
		""" returns a python list of qModelIndices """
		if not indices:
			print( "no entries selected to copy" )
			return
		index = indices[0] # only copying single entry for now


		mime = self.modelObject.mimeData( [index] )
		# print( "copy mime {}".format(mime.text()))
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




	def showMenu(self, *args, **kwargs):
		return self.menu.exec_(*args, **kwargs)


	def dragEnterEvent(self, event):
		
		super(TileSettings, self).dragEnterEvent(event)
		# event.accept()
		
		
	def dragMoveEvent(self, event):
		
		super(TileSettings, self).dragMoveEvent(event)
		# event.accept()

	def saveAppearance(self):
		""" saves expansion and selection state """

	def restoreAppearance(self):
		""" restores expansion and selection state """

	def keyPressEvent(self, event):
		""" bulk of navigation operations,
		for hierarchy navigation aim to emulate maya outliner

		ctrl+D - duplicate
		del - delete

		left/right - select siblings
		up / down - select child / parent

		p - parent selected branches to last selected
		shiftP - parent selected branches to root

		ctrl + shift + left / right - shuffle selected among siblings

		channel as much of this as possible through the base tree object

		not sure if there is an elegant way to structure this
		going with battery of if statements

		"""
		sel = self.selectionModel().selectedRows()
		#print("sel {}".format(sel))
		# don't override anything if editing is in progress
		if self.state() == QtWidgets.QTreeView.EditingState or len(sel) == 0:
			return super(TileSettings, self).keyPressEvent(event)
		refresh = True
		try:
			# very important that event methods don't error,
			# messes up whole maya ui if they do
			# print(self.modelObject.treeIndices())

			if event.modifiers() and QtCore.Qt.ControlModifier:
				if event.key() == QtCore.Qt.Key_D: # duplicate
					for row in sel:
						self.modelObject.duplicateRow(row)
						return True

				# shifting row up or down
				if QtCore.Qt.ShiftModifier:
					if event.key() in [QtCore.Qt.Key_Up, QtCore.Qt.Key_Left]:
						for row in sel:
							self.modelObject.shiftRow(row, up=True)
					elif event.key() in [QtCore.Qt.Key_Down, QtCore.Qt.Key_Right]:
						for row in sel:
							self.modelObject.shiftRow(row, up=False)
					self.expandAll()
					return True


			elif event.key() == QtCore.Qt.Key_Delete:
				for row in sel:
					self.modelObject.deleteRow(row)
					self.expandAll()
					return True


			# direction keys to move cursor
			if event.key() == QtCore.Qt.Key_Left:
				# back one index
				return True
			elif event.key() == QtCore.Qt.Key_Right:
				# forwards one index
				return True
			elif event.key() == QtCore.Qt.Key_Up:
				# up to parent
				pass
			elif event.key() == QtCore.Qt.Key_Down:
				# down to child
				pass


			# for i in sel:
			# 	#print("i {}".format(i)) # returns model indices
			# 	#print(self.modelObject.itemData(i))
			# 	address = self.modelObject.data(i, objRole)
			# 	print(address)
			# 	# print(self.tree[address])
			# 	# print(self.tree(address).value) # works
			# 	""" itemData returns
			# 	{0: u'parent'} - string name of branch with no address data
			# 	"""
			# 	# print(self.modelObject.treeIndices())


			# delete rows
			elif event.key() == QtCore.Qt.Key_Delete:
				for i in sel:
					branch = self.modelObject.branchFromIndex(i)
					branch.remove()
				refresh = True


			if refresh:
				#self.sync()
				pass

		except Exception as e:
			raise
		finally:
			return super(TileSettings, self).keyPressEvent(event)

	def focusNextPrevChild(self, direction):
		return False

	def setTree(self, tree):
		"""associates widget with AbstractTree object"""
		self.tree = tree
		self.root = tree.root
		tree.valueChanged.connect(self.contentChanged)
		tree.structureChanged.connect(self.contentChanged)

		self.modelObject = AbstractTreeModel(tree=self.tree)
		self.setModel(self.modelObject)

		# self.resizeToTree()
		self.expandAll()

		return self.modelObject


	def sync(self):
		#self.setTree(self.tree)
		self.modelObject.sync()


	def addHighlight(self, address, kind):
		"""adds a highlight to TreeView line, depending on reason"""
		colour = QtCore.QColor(self.highlightKind[kind])
		self.highlights[address] = kind


	def initActions(self):
		"""sets up copy, add, delete etc actions for branch entries"""


class AbstractBranchItem(QtGui.QStandardItem):
	"""small wrapper allowing standardItems to take tree objects directly"""
	ICONS = {}

	def __init__(self, tree):
		""":param tree : AbstractTree"""
		super(AbstractBranchItem, self).__init__(tree.name)
		self.tree = tree or AbstractTree()
		self.treeType = AbstractTree # add support here for subclasses if necessary
		self.setColumnCount(1)
		self.trueType = type(self.tree.name)

		self.icon = tree.extras.get("icon")
		if self.icon and self.icon in self.ICONS:
			self.icon = QtGui.QIcon(self.icon)

		#self.addValueData()


	def data(self, role=QtCore.Qt.DisplayRole):
		""" just return branch name
		data is used when regenerating abstractTree from model"""
		if role == objRole:
			#return self.tree # crashes
			return self.tree.address
		base = super(AbstractBranchItem, self).data(role)
		return base

	def setData(self, value, role): # sets the NAME of the tree
		name = self.tree._setName(value) # role is irrelevant
		self.emitDataChanged()
		return super(AbstractBranchItem, self).setData(name, role)


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

	# def columnCount(self):
	# 	return 2
	#
	# def column(self):
	# 	return 0
	#
	# def rowCount(self):
	# 	return len(self.tree.branches)
	# 	#return 1
	#
	# def row(self):
	# 	return len(self.parents())

	""" for all row operations we EXPECT a row unit to be [branchItem, valueItem] """
	#
	# def removeRows(self, row, count):
	# 	""" remove tree objects from parent """
	# 	for i in range(count):
	# 		index = row + i
	# 		self.removeRow(index)
	#
	# def removeRow(self, row):
	# 	branch = self.tree.branches[row]
	# 	branch.remove()
	# 	return super(AbstractBranchItem, self).removeRow(row)
	#
	# def insertRows(self, row, items):
	# 	""" overloaded function, items may be int or list of items """
	# 	self.model().beginInsertRows(row, row + len(items))
	# 	if isinstance(items, int):
	# 		return super(AbstractBranchItem, self).insertRows(row, items)
	# 	# add branch items to tree
	# 	for i in range(len(items)):
	# 		index = row + i
	# 		super(AbstractBranchItem, self).insertRows(index, items[i])
	# 	self.model().endInsertRows()
	# def insertRow(self, row, item):
	# 	print("inserting row {}".format(item))
	# 	print("at index {}".format(row))
	# 	super(AbstractBranchItem, self).insertRow(row, item)
	# 	tree = item.data(objRole)
	# 	print( "tree {}".format(tree.display()))
	# 	if tree not in self.tree.branches:
	# 		self.tree.addChild(tree, index=row)
	# 	#self.model().itemChanged.emit(self)
	# 	return
	#
	# def appendRows(self, items):
	# 	for i in items:
	# 		self.appendRow(i)
	# def appendRow(self, item):
	# 	return self.insertRow( self.rowCount() - 1, item)

	def parents(self):
		""" returns chain of branch items to root """
		if self.parent():
			return [self.parent()] + self.parent().parents()
		return []


	# def clone(self):
	# 	""" return new key : value row """
	# 	newBranch = self.treeType.fromDict( self.tree.serialise )

	def __repr__(self):
		return "<BranchItem {}>".format(self.data())


class AbstractValueItem(QtGui.QStandardItem):
	"""overly specific but it's fine
	differentiate branch tag from actual value"""
	def __init__(self, tree):
		self.tree = tree
		self.trueType = type(self.tree.value)
		value = self.processValue(self.tree.value)

		super(AbstractValueItem, self).__init__(value)

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

	def data(self, role=QtCore.Qt.DisplayRole):
		base = super(AbstractValueItem, self).data(role)
		return base

	def rowCount(self):
		return 0
	def columnCount(self):
		return 0

	def column(self):
		return 1

	def __repr__(self):
		return "<ValueItem {}>".format(self.data())


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
			print("eval'd info is {}".format(info)) # evals to a dict

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

			self.endInsertRows()

			# destroy parent tree branches and rebuild from model

			print( "dropped tree value is {}".format( tree.value))

		return True

	def branchFromIndex(self, index):
		""" returns tree object associated with qModelIndex """
		return self.itemFromIndex(index).tree

	def columnCount(self, index):
		"""  only ever key : value """
		return 2
		pass

	def rowCount(self, index):
		# called on resizeevents too

		#print("rowcount index {}".format(index))

		# root item gives
		# <PySide2.QtCore.QModelIndex(-1,-1,0x0,QObject(0x0))  at 0x000000005B01BE88> #
		if index.column() == index.row() == -1:
			# root item
			return len(self.tree.root.allBranches())

		# no rows under value
		if index.column() > 0: # this is a value item
			return 0
		return len(self.tree.root.allBranches())
		#return len(self.itemFromIndex(index).tree.branches)
		pass
	#
	# # def createIndex(self, row, column):
	# # 	pass
	#
	# def data(self, index, role=QtCore.Qt.DisplayRole):
	# 	pass
	#
	# def itemFromIndex(self, index):
	# 	pass
	#
	# def indexFromItem(self, item):
	# 	""" :param item : abstractTree branch """
	#
	# 	pass


	def rowFromTree(self, tree):
		""" returns index corresponding to tree """
		branchItem = AbstractBranchItem(tree)
		valueItem = AbstractValueItem(tree)
		return [branchItem, valueItem]

	def treeFromRow(self, row):
		""":rtype AbstractTree """
		return self.tree( self.data(row, objRole) )


	def duplicateRow(self, row):
		""" copies tree, increments its name, adds it as sibling
		:param row : QModelIndex for row """

		parent = row.parent()
		address = self.data(row, objRole)
		tree = self.tree(address)
		treeParent = tree.parent
		newTree = tree.fromDict( tree.serialise() )
		newTree = treeParent.addChild( newTree )

		self.buildFromTree(newTree, parent=self.itemFromIndex(parent))

	def shiftRow(self, row, up=True):
		""" shifts row within its siblings up or down """
		tree = self.treeFromRow(row)
		parent = tree.parent
		startIndex = tree.index()
		newIndex = max(0, min( len(parent.branches), startIndex + (-1 if up else 1)))
		tree.setIndex(newIndex)
		self.sync()



	def deleteRow(self, row):
		""" removes tree branch, then removes item """

		tree = self.tree( self.data(row, objRole) )
		tree.remove()
		# self.beginRemoveRows(row.parent(), row.row() - 1, row.row())
		# self.removeRow( row )
		# self.endRemoveRows()
		self.sync()



	def buildFromModel(self, parentItem, parentTree=None):
		"""rebuilds a section of the abstractTree from the ui model
		:param parentItem : parent standardItem below which to rebuild"""

		for i in range(parentItem.rowCount()):
			child = parentItem.child(i)
			print( "model child is {}".format(child))




	def setTree(self, tree):
		self.tree = tree
		self.clear()
		self.root = AbstractBranchItem(tree.root)
		rootRow = [self.root, AbstractValueItem(tree)]

		#self.root = self.invisibleRootItem()
		#self.root.tree = tree.root
		#self.beginResetModel()
		self.appendRow(rootRow)
		for i in self.tree.branches:
			self.buildFromTree(i, parent=self.root)
		#self.endResetModel()


		#print("rowCount {}".format(self.rowCount(self.invisibleRootItem().index())))


	def buildFromTree(self, tree, parent=None):
		""":param tree : AbstractTree
		:param parent : AbstractBranchItem below which to build"""
		branchItem = AbstractBranchItem(tree=tree)
		textItem = AbstractValueItem(tree)

		parent.appendRow( [branchItem, textItem] )
		#parent.appendRow( branchItem )
		for i in tree.branches:
			self.buildFromTree(i, parent=branchItem)
		self.itemChanged.emit(branchItem)
		return branchItem


	def sync(self):
		""" synchronises qt model from tree object,
		never directly other way round
		"""
		# store currently selected rows and columns, order doesn't matter
		selectionModel = QtCore.QItemSelectionModel(model=self)
		print(selectionModel.selectedIndexes())
		oldHashes = [ hash(self.itemFromIndex(i).tree) for i in selectionModel.selectedIndexes()]
		selectionModel.clear()
		self.clear()
		self.setTree(self.tree)
		# for index in self.treeIndices():
		# 	if hash(self.itemFromIndex(index).tree) in oldHashes:
		# 		selectionModel.select(index, QtCore.QItemSelectionModel.Select)
		# 		#selectionModel.select(index, QtCore.QItemSelectionModel.SelectCurrent)
		# 		#selectionModel.select(index, QtCore.QItemSelectionModel.Current)


class EditTree(QtWidgets.QUndoCommand):

	def __init__(self, tree):
		newData = None
		prevData = None
		pass

	def redo(self):
		""" set tree from new data """

	def undo(self):
		""" set tree from prev data """


def test():
	from edRig.lib.python import testTree

	# sys.path.append("C:\Program Files\Autodesk\Maya2018\Python\Lib\site-packages\PySide2")

	# import PySide2

	# win = QtWidgets.QMainWindow()
	# widg = TileSettings(None, tree=testTree)
	# #widg.setTree(testTree)
	# win.setCentralWidget(widg)
	# ref = win.show()
	win = BaseMayaUi(parent=getMayaMainWindow())
	widg = TileSettings(win, tree=testTree)

	#return ref, win
	return win.show()

if __name__ == "__main__":
	# test the tree widget
	#print("ey")
	#import sys
	test()

