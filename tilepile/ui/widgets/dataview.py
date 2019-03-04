# t i m e _ t o _ h a c k

from PySide2 import QtCore, QtWidgets, QtGui, QtXml


class DataViewWidget(QtWidgets.QTreeWidget):
	"""widget for viewing an op's data dict
	THIS DOES NOT INTERACT WITH THE FILE SYSTEM
	the op affects the file, this affects the op"""

	# ADD CAPABILITY TO ADD AND REMOVE ENTRIES

	contentChanged = QtCore.Signal()
	resizeWidget = QtCore.Signal()
	op = None
	opData = {}

	def __init__(self, parent=None):
		super(DataViewWidget, self).__init__(parent)
		self.setAnimated(True)  # swag
		self.setAutoExpandDelay(1)

		self.itemChanged.connect(self.contentChanged)

		self.saveButton = QtWidgets.QPushButton(self)
		self.saveButton.setText("save")
		self.saveButton.clicked.connect(self.updateOpData)

	def currentDataAsDict(self):
		print "currentDataAsDict"
		# top = self.topLevelItem(0)
		top = self.invisibleRootItem()
		# print "top is {}".format(top)
		# if not top:
		# return None
		d = {}
		d.clear()
		# d = self.toDict(parent=top)
		self.toDict(parent=top, targetDict=d)
		print "toDict result is {}".format(d)
		return d

	def flags(self, index):
		"""everything is editable"""
		return (QtCore.Qt.ItemIsEnabled |
		        QtCore.Qt.ItemIsSelectable |
		        QtCore.Qt.ItemIsEditable)

	def updateOpData(self):
		print "updateOpData"
		# print "currentOpData is {}".format(self.op.data)
		currentDict = self.currentDataAsDict()
		# print "currentDict is {}".format(currentDict)
		# self.opData = currentDict
		self.op.data.clear()
		# self.op.data = currentDict
		self.op.data.update(currentDict)
		currentDict.clear()
		print "new opData is {}".format(self.op.data)
		self.clearQTreeWidget(self)

	def setOp(self, op=None):
		print ""
		# print "setting op"
		# print "passed op is {}".format(op)
		self.opData.clear()
		if isinstance(op, list):
			op = op[-1]
		print "op is {}".format(op)

		self.op = None
		self.clearQTreeWidget(self)
		# print "current dataview is {}".format(self.currentDataAsDict())

		self.op = op
		self.refresh(self.op.data)
		# print "current dataview is {}".format(self.currentDataAsDict())

	def refresh(self, value={"blank": "dict"}):
		print "refreshing"
		self.clearQTreeWidget(self)
		self.fill_item(self.invisibleRootItem(), value)
		self.expandAll()

	def toDict(self, targetDict={}, parent=None):
		# this bit's all mine, and i'm very proud of it
		# d = OrderedDict()
		# print ""
		if not parent:
			parent = self.invisibleRootItem()
		d = {}
		d.clear()
		if parent.childCount():

			if parent.data(0, 0):
				d[parent.data(0, 0)] = {}
				childDict = d[parent.data(0, 0)]
			else:
				childDict = d
			# d[parent.data(0,0)] = {}
			valList = []

			for i in range(parent.childCount()):
				child = parent.child(i)
				childData = child.data(0, 0)
				print "child data is {}".format(child.data(0, 0))
				if child.childCount():
					# self.toDict(targetDict=d[parent.data(0,0)], parent=child)
					self.toDict(targetDict=childDict, parent=child)
				elif isinstance(childData, list):
					for i in childData:
						self.toDict(targetDict=childDict, parent=child)
				else:
					valList.append(child.data(0, 0))
					if len(valList) == 1:
						valList = valList[0]
					d[parent.data(0, 0)] = valList
					# childDict = valList

		# if isinstance(targetDict, dict):
		targetDict.update(d)
		return targetDict

	def fill_item(self, item, value):
		def new_item(parent, text, val=None):
			child = QtWidgets.QTreeWidgetItem([text])
			child.setFlags((QtCore.Qt.ItemIsEnabled |
			                QtCore.Qt.ItemIsSelectable |
			                QtCore.Qt.ItemIsEditable))
			self.fill_item(child, val)
			parent.addChild(child)
			child.setExpanded(True)

		if value is None:
			return
		elif isinstance(value, dict):
			for key, val in sorted(value.items()):
				new_item(item, str(key), val)
		elif isinstance(value, (list, tuple)):
			for i, val in enumerate(value):
				new_item(item, str(i), val=val)
		# for val in value:
		#     text = (str(val) if not isinstance(val, (dict, list, tuple))
		#             else '[%s]' % type(val).__name__)
		#     new_item(item, text, val=None)
		else:
			new_item(item, str(value))

	def clearQTreeWidget(self, treeWidget):
		iterator = QtWidgets.QTreeWidgetItemIterator(treeWidget, QtWidgets.QTreeWidgetItemIterator.All)
		while iterator.value():
			iterator.value().takeChildren()
			iterator += 1
		i = treeWidget.topLevelItemCount() + 1
		if i == 0:
			return
		# print "original topLevelItemCount is {}".format(treeWidget.topLevelItemCount())
		while i >= 0:
			treeWidget.takeTopLevelItem(i)
			# print "topLevelItemCount is {}".format(treeWidget.topLevelItemCount())
			i = i - 1
