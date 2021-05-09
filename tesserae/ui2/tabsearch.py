#!/usr/bin/python
from PySide2 import QtCore, QtWidgets, QtGui



class TabSearchCompleter(QtWidgets.QCompleter):
	"""
	QCompleter adapted from:
	https://stackoverflow.com/questions/5129211/qcompleter-custom-completion-rules
	"""

	def __init__(self, nodes=None, parent=None):
		super(TabSearchCompleter, self).__init__(nodes, parent)
		self.setCompletionMode(self.PopupCompletion)
		self.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self._local_completion_prefix = ''
		self._using_origmodel = False
		self._sourcemodel = None
		self._filtermodel = None


	def splitPath(self, path):
		self._local_completion_prefix = path
		self.updateModel()
		if self._filtermodel.rowCount() == 0:
			self._using_origmodel = False
			self._filtermodel.setSourceModel(QtCore.QStringListModel([path]))
			return [path]
		return []

	def updateModel(self):
		if not self._using_origmodel:
			self._filtermodel.setSourceModel(self._sourcemodel)

		pattern = QtCore.QRegExp(self._local_completion_prefix,
								 QtCore.Qt.CaseInsensitive,
								 QtCore.QRegExp.FixedString)
		self._filtermodel.setFilterRegExp(pattern)

	def setModel(self, model):
		self._sourcemodel = model
		self._filtermodel = QtCore.QSortFilterProxyModel(self)
		self._filtermodel.setSourceModel(self._sourcemodel)
		super(TabSearchCompleter, self).setModel(self._filtermodel)
		self._using_origmodel = True

class AbstractSearchWidget(QtWidgets.QLineEdit):
	"""general implementation"""
	
	search_submitted = QtCore.Signal(str)
	
	def __init__(self, parent=None, items=None):
		super(AbstractSearchWidget, self).__init__(parent)
		self.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)

		self.nodeNames = sorted(items or [])

		self.stringModel = QtCore.QStringListModel(items, self)
		self.completerWidg = TabSearchCompleter()
		self.completerWidg.setModel(self.stringModel)
		self.setCompleter(self.completerWidg)
		if items:
			self.setItems(items)



		self.returnPressed.connect(self._on_search_submitted)

	def setItems(self, items=None):
		"""set completer options"""
		self.nodeNames = items or []
		self.stringModel.setStringList(self.nodeNames)
		self.completerWidg.setModel(self.stringModel)

	def showEvent(self, event):
		super().showEvent(event)
		self.setSelection(0, len(self.text()))
		self.setFocus()
		print(self.nodeNames)


	def _on_search_submitted(self):
		text = self.text()
		self.search_submitted.emit(text)
		self.close()
		self.parentWidget().clearFocus()


class TabSearchWidget(AbstractSearchWidget):
	"""originally emitted a node type - now just pass and emit strings,
	processed centrally"""

	# def __init__(self, parent=None, nodeNames=None):
	# 	super(TabSearchWidget, self).__init__(parent=parent, items=nodeNames)
	#
	# 	self.setMinimumSize(200, 22)
	# 	self.setTextMargins(2, 0, 2, 0)
	# 	self.hide()
	#
	# def showEvent(self, event):
	# 	super(TabSearchWidget, self).showEvent(event)
	# 	self.setSelection(0, len(self.text()))
	# 	self.setFocus()
	# 	print(self.nodeNames)
	#
	# def set_nodes(self, nodeNames=None):
	# 	super(TabSearchWidget, self).setItems(nodeNames)
	#
	# def _on_search_submitted(self):
	# 	super(TabSearchWidget, self)._on_search_submitted()
	# 	self.close()
	# 	self.parentWidget().clearFocus()