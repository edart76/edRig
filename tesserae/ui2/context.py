"""gargantuan context menu keeping rest of ui clear"""

from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
from functools import partial

from PySide2 import QtCore, QtGui, QtWidgets
#from edRig.tesserae.jchan2.widgets.stylesheet import STYLE_QMENU
from edRig.tesserae.action import Action
from edRig.tesserae.ui2.style import STYLE_QMENU
#from edRig.tesserae.ui2.lib import ContextMenu

from edRig.lib.python import AbstractTree

#EmbeddedAction = EmbeddedAction
#ContextMenu = ContextMenu

class ContextMenu(object):
	"""this is no reason this doesn't inherit from qmenu now,
	but it already works fine"""

	def __init__(self, view, title=None):
		self.view = view
		# self.rootMenu = menu or QtWidgets.QMenu("Take action:")
		self.rootMenu = QtWidgets.QMenu("Take action:", parent=self.view)
		if title: self.rootMenu.setTitle( title )

	def exec_(self, pos=None):
		"""allows smaller menus to return only the selected action
		for computation by outer code, or for a subclassed menu
		to be implemented with more thorough internal computation"""
		return self.rootMenu.exec_(pos)

	def addAction(self, action=None, func=None):
		# action.setShortcutVisibleInContextMenu(True)
		if func and not action:
			#action = ActionItem(execDict={"func" : func})
			action = Action(func)
		self.addSubAction(action)

	def addMenu(self, name):
		menu = QtWidgets.QMenu(None, title=name)
		menu.setStyleSheet(STYLE_QMENU)
		self.rootMenu.addMenu(menu)
		return ContextMenu(self.view, menu)

	# return menu

	def addSubMenu(self, name="", parent=None):
		menu = QtWidgets.QMenu(None, title=name)
		menu.setStyleSheet(STYLE_QMENU)
		parent.addMenu(menu)
		return menu

	def addSubAction(self, actionObject:Action=None,
	                 actionPartial:partial=None, name=None,
	                 parent=None):
		#print("add sub action", actionObject, name, parent)
		if not parent:
			parent = self.rootMenu

		newAction = QtWidgets.QAction(parent=parent)

		if actionObject:
			name = name or actionObject.name
			#newAction.triggered.connect(self.marker)
			def _inner(*args, **kwargs):
				actionObject.execute()
			newAction.triggered.connect(_inner)
		else:
			name = name or actionPartial.func.__name__
			newAction.triggered.connect(actionPartial)

		newAction.setText(name)
		parent.addAction(newAction)
		return newAction

	def marker(self, *args, **kwargs):
		print( "TRIGGERING ACTION")

	def addCommand(self, name, func=None, shortcut=None, parent=None):
		if not parent:
			parent = self.rootMenu
		action = QtWidgets.QAction(name, self.view)
		# action.setShortcutVisibleInContextMenu(True)
		if shortcut:
			action.setShortcut(shortcut)
		if func:
			action.triggered.connect(func)
		parent.addAction(action, shortcut=shortcut)
		return action

	def addSeparator(self):
		self.rootMenu.addSeparator()

	def addSection(self, *args):
		self.rootMenu.addSection(*args)

	def buildMenusFromDict(self, menuDict=None):
		"""updates context menu with any action passed to it
		"""
		self.rootMenu.addSeparator()
		try:
			#print( "context menuDict is {}".format(menuDict))
			self.buildMenu(menuDict=menuDict, parent=self.rootMenu)
		except Exception as e:
			raise e
			pass

	def buildMenu(self, menuDict=None, parent=None):
		"""builds menu recursively from keys in dict
		currently expects actionItems as leaves"""
		# print ""
		menuDict = menuDict or {}
		if isinstance(menuDict, list):
			for i in menuDict:
				self.addSubAction(i, name=i.name)
		for k, v in menuDict.items():
			#print "k is {}, v is {}".format(k, v)
			if isinstance(v, dict):
				#print "buildMenu v is dict {}".format(v)
				if not list(v.keys()):
				#	print "skipping"
					continue
				newParent = self.addSubMenu(name=k, parent=parent)
				self.buildMenu(v, parent=newParent)
			elif isinstance(v, list):
				for i in v:
					self.buildMenu(i, parent=parent)

			elif isinstance(v, Action):
				action = self.addSubAction(parent=parent, actionObject=v)
		pass

	def buildMenusFromTree(self, actionTree:AbstractTree, parent=None):
		""" builds recursively from tree
		only actions at leaves are considered """

		if actionTree.branches: # add menu for multiple actions
			parent = self.addSubMenu(name=actionTree.name,
			                         parent=parent or self.rootMenu)
			for branch in actionTree.branches:
				self.buildMenusFromTree(branch, parent)
			return parent
		else: # add single entry for single action
			if isinstance(actionTree.value, (Action)):
				action = self.addSubAction(actionObject=actionTree.value,
				                           parent=parent)
			elif isinstance(actionTree.value, partial):
				action = self.addSubAction(actionPartial=actionTree.value,
				                           parent=parent)
			elif isinstance(actionTree.value, function):
				action = self.addSubAction(
					actionPartial=partial(func=actionTree.value),
				    parent=parent)



	def clearCustomEntries(self):
		"""clear only custom actions eventually -
		for now clear everything"""
		self.rootMenu.clear()
