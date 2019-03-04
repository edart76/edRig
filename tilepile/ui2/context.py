"""gargantuan context menu keeping rest of ui clear"""
from PySide2 import QtCore, QtGui, QtWidgets
from edRig.structures import ActionItem, ActionList
#from edRig.tilepile.jchan2.widgets.stylesheet import STYLE_QMENU
from edRig.tilepile.ui2.style import STYLE_QMENU
from edRig.tilepile.ui2.lib import EmbeddedAction, ContextMenu

EmbeddedAction = EmbeddedAction
ContextMenu = ContextMenu
#
# class EmbeddedAction(QtWidgets.QAction):
# 	"""the bridge between normal action items and qt"""
# 	def __init__(self, actionObject=None, parent=None):
# 		super(EmbeddedAction, self).__init__(parent)
# 		self._actionObject = actionObject or None
# 		if not self._actionObject:
# 			print "no actionObject received for embedded action!"
# 			return
# 		self.name = self._actionObject.name
# 		if isinstance(self._actionObject, ActionItem):
# 			self.triggered.connect(self._actionObject.execute)
# 		elif isinstance(self._actionObject, ActionList):
# 			self.triggered.connect(self._actionObject.executeAll)
#
#
#
# class ContextMenu(object):
# 	"""this is no reason this doesn't inherit from qmenu now,
# 	but it already works fine"""
#
# 	def __init__(self, view, menu=None):
# 		self.view = view
# 		# self.rootMenu = menu or QtWidgets.QMenu("Take action:")
# 		self.rootMenu = QtWidgets.QMenu("Take action:")
#
# 	def exec_(self, pos):
# 		self.rootMenu.exec_(pos)
#
# 	#
# 	# def get_menu(self, name):
# 	# 	ctx_menu = self.view.context_menu()
# 	# 	root_menu = ctx_menu._menu_obj
# 	# 	for action in root_menu.actions():
# 	# 		if action.text() != name:
# 	# 			continue
# 	# 		menu = action.menu()
# 	# 		return ContextMenu(self.view, menu)
#
# 	def add_action(self, action):
# 		#action.setShortcutVisibleInContextMenu(True)
# 		self.rootMenu.addAction(action)
#
# 	def add_menu(self, name):
# 		menu = QtWidgets.QMenu(None, title=name)
# 		menu.setStyleSheet(STYLE_QMENU)
# 		self.rootMenu.addMenu(menu)
# 		return ContextMenu(self.view, menu)
# 		#return menu
#
# 	def addSubMenu(self, name="", parent=None):
# 		menu = QtWidgets.QMenu(None, title=name)
# 		menu.setStyleSheet(STYLE_QMENU)
# 		parent.addMenu(menu)
# 		return menu
#
# 	def addSubAction(self, actionObject=None, parent=None):
# 		"""not robust at all but idgaf"""
# 		if not parent:
# 			parent = self.rootMenu
# 		if isinstance(actionObject, ActionList):
# 			for i in actionObject.getActions():
# 				self.addSubAction(i, parent=parent)
# 				return
# 		newAction = EmbeddedAction(actionObject=actionObject, parent=parent)
# 		newAction.setText(newAction.name)
# 		parent.addAction(newAction)
#
#
# 	def add_command(self, name, func=None, shortcut=None):
# 		action = QtWidgets.QAction(name, self.view)
# 		#action.setShortcutVisibleInContextMenu(True)
# 		if shortcut:
# 			action.setShortcut(shortcut)
# 		if func:
# 			action.triggered.connect(func)
# 		self.rootMenu.addAction(action, shortcut=shortcut)
#
# 	def add_separator(self):
# 		self.rootMenu.addSeparator()
#
# 	def buildMenusFromDict(self, menuDict=None):
# 		"""updates context menu with any action passed to it
# 		"""
#
# 		self.rootMenu.addSeparator()
# 		try:
# 			self.buildMenu(menuDict=menuDict, parent=self.rootMenu)
# 		except RuntimeError("SOMETHING WENT WRONG WITH CONTEXT MENU"):
# 			pass
#
#
# 	"""CONTEXT MENU ACTIONS for allowing procedural function execution"""
# 	def buildMenu(self, menuDict={}, parent=None):
# 		"""builds menu recursively from keys in dict
# 		currently expects actionItems as leaves"""
# 		for k, v in menuDict.iteritems():
# 			if isinstance(v, dict):
# 				newParent = self.addSubMenu(name=k, parent=parent)
# 				self.buildMenu(v, parent=newParent)
# 			elif isinstance(v, list):
# 				for i in v:
# 					self.buildMenu(i, parent=parent)
#
# 			elif isinstance(v, ActionItem) or isinstance(v, ActionList):
# 				self.addSubAction(parent=parent, actionObject=v)
# 		pass
#
# 	def clearCustomEntries(self):
# 		"""clear only custom actions eventually -
# 		for now clear everything"""
# 		self.rootMenu.clear()
#
#
#
#
