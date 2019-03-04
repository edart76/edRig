
from PySide2 import QtCore, QtGui, QtWidgets
from edRig.tilepile.jchan2.widgets.stylesheet import STYLE_QMENU
from edRig.layers.action import ActionItem, ActionList
# encapsulation is dead and i killed it


class EmbeddedAction(QtWidgets.QAction):
	"""the bridge between normal action items and qt"""
	def __init__(self, actionObject=None, parent=None):
		super(EmbeddedAction, self).__init__(parent)
		self._actionObject = actionObject or None
		if not self._actionObject:
			print "no actionObject received for embedded action!"
			return
		self.name = self._actionObject.name
		if isinstance(self._actionObject, ActionItem):
			self.triggered.connect(self._actionObject.execute)
		elif isinstance(self._actionObject, ActionList):
			self.triggered.connect(self._actionObject.executeAll)



class ContextMenu(object):

	def __init__(self, view, menu):
		self.__view = view
		self.__menu = menu

	@property
	def _menu_obj(self):
		return self.__menu

	def get_menu(self, name):
		ctx_menu = self.__view.context_menu()
		root_menu = ctx_menu._menu_obj
		for action in root_menu.actions():
			if action.text() != name:
				continue
			menu = action.menu()
			return ContextMenu(self.__view, menu)

	def add_action(self, action):
		#action.setShortcutVisibleInContextMenu(True)
		self.__menu.addAction(action)

	def add_menu(self, name):
		menu = QtWidgets.QMenu(None, title=name)
		menu.setStyleSheet(STYLE_QMENU)
		self.__menu.addMenu(menu)
		return ContextMenu(self.__view, menu)
		#return menu

	def addSubMenu(self, name="", parent=None):
		menu = QtWidgets.QMenu(None, title=name)
		menu.setStyleSheet(STYLE_QMENU)
		parent.addMenu(menu)
		return menu

	def addSubAction(self, actionObject=None, parent=None):
		"""not robust at all but idgaf"""
		newAction = EmbeddedAction(actionObject=actionObject, parent=parent)
		newAction.setText(newAction.name)
		parent.addAction(newAction)


	def add_command(self, name, func=None, shortcut=None):
		action = QtWidgets.QAction(name, self.__view)
		#action.setShortcutVisibleInContextMenu(True)
		if shortcut:
			action.setShortcut(shortcut)
		if func:
			action.triggered.connect(func)
		self.__menu.addAction(action, shortcut=shortcut)

	def add_separator(self):
		self.__menu.addSeparator()

	def buildMenusFromDict(self, menuDict=None):
		"""updates context menu with any action passed to it"""
		self.__menu.addSeparator()
		try:
			self.buildMenu(menuDict=menuDict, parent=self.__menu)
		except RuntimeError("SOMETHING WENT WRONG WITH CONTEXT MENU"):
			pass


	"""CONTEXT MENU ACTIONS for allowing procedural function execution"""
	def buildMenu(self, menuDict={}, parent=None):
		"""builds menu recursively from keys in dict
		currently expects actionItems as leaves"""
		for k, v in menuDict.iteritems():
			if isinstance(v, dict):
				newParent = self.addSubMenu(name=k, parent=parent)
				self.buildMenu(v, parent=newParent)

			elif isinstance(v, ActionItem) or isinstance(v, ActionList):
				self.addSubAction(parent=parent, actionObject=v)
		pass

	def clearCustomEntries(self):
		"""clear only custom actions eventually -
		for now clear everything"""
		self._menu_obj.clear()

	# @staticmethod
	# def executeAction(execDict={}):
	# 	"""expects a dict of format: {
	# 		"func" : function to execute,
	# 		"args" : guess,
	# 		"kwargs" : guess again }
	# 	will then execute a void function with passed args and kwargs"""
	# 	if not "func" in execDict.keys():
	# 		return
	# 	args = execDict["args"] if "args" in execDict.keys() else None
	# 	kwargs = execDict["kwargs"] if "kwargs" in execDict.keys() else {"blank" : None}
	# 	execDict["func"](*args, **kwargs)
	# 	return 1
	# 	# make sure all action functions have *args and **kwargs

	# BEWARE on building action menus - two actions with same name should be
	# represented by single heading, but both functions should be executed

	# nope, dealt with prior
