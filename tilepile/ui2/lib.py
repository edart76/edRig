# reusable ui items
from PySide2 import QtWidgets, QtCore
from edRig.structures import ActionItem, ActionList
# from edRig.tilepile.jchan2.widgets.stylesheet import STYLE_QMENU
from edRig.tilepile.ui2.style import STYLE_QMENU
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as omui
import shiboken2, weakref
import maya.cmds as cmds
from shiboken2 import wrapInstance
import pprint
# https://github.com/mottosso/Qt.py by Marcus Ottosson

def getMayaWindow():
	pointer = omui.MQtUtil.mainWindow()
	return shiboken2.wrapInstance(long(pointer), QtWidgets.QWidget)


'''
Template class for docking a Qt widget to maya 2017+.
Author: Lior ben horin
12-1-2017
'''

def dock_window(dialog_class):
	try:
		cmds.deleteUI(dialog_class.CONTROL_NAME)
	except:
		pass

	# building the workspace control with maya.cmds
	main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME,
	                                     #ttc=["AttributeEditor", -1],
	                                     iw=1000, #mw=False,
	                                     initialHeight=800,
										 wp='free',
										 label=dialog_class.DOCK_LABEL_NAME)

	# now lets get a C++ pointer to it using OpenMaya
	control_widget = omui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
	# conver the C++ pointer to Qt object we can use
	control_wrap = wrapInstance(long(control_widget), QtWidgets.QWidget)

	# control_wrap is the widget of the docking window and now we can start working with it:
	control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
	win = dialog_class(control_wrap)

	# after maya is ready we should restore the window since it may not be visible
	cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control,
	                                                      e=True, rs=True))
	# will return the class of the dock content.
	return win.run()


class MyDockingUI(QtWidgets.QWidget):
	instances = list()
	CONTROL_NAME = 'base_control'
	DOCK_LABEL_NAME = 'base control'

	def __init__(self, parent=None):
		super(MyDockingUI, self).__init__(parent)

		# let's keep track of our docks so we only have one at a time.
		MyDockingUI.delete_instances()
		self.__class__.instances.append(weakref.proxy(self))

		self.window_name = self.CONTROL_NAME

	@staticmethod
	def delete_instances():
		for ins in MyDockingUI.instances:
			try:
				ins.setParent(None)
				ins.deleteLater()
			except:
				# ignore the fact that the actual parent has already been deleted by Maya...
				pass

			MyDockingUI.instances.remove(ins)
			del ins

	def run(self):
		return self

class MayaDockWindow(MayaQWidgetDockableMixin, QtWidgets.QWidget):
	"""base class for dockable maya windows"""
	def __init__(self, parent=None):
		super(self.__class__, self).__init__(parent)
		self.mayaMainWindow = getMayaWindow()
		self.setWindowFlags(QtCore.Qt.Window)

	def dockCloseEventTriggered(self):
		pass

class ConfirmDialogue(QtWidgets.QMessageBox):
	"""convenience for confirmation"""
	def __init__(self, *args, **kwargs):
		super(ConfirmDialogue, self).__init__(args, kwargs)

	@staticmethod
	def confirm(parent=None, title="Confirm", message="are you sure about that",
				no="good point", yes="did i stutter"):
		flags = QtWidgets.QMessageBox.StandardButton.No
		flags |= QtWidgets.QMessageBox.StandardButton.Yes
		result = ConfirmDialogue.question(parent, title, message, flags)
		if result == QtWidgets.QMessageBox.Yes:
			return True
		else:
			return



class EmbeddedAction(QtWidgets.QAction):
	"""the bridge between normal action items and qt"""

	def __init__(self, actionObject=None, parent=None):
		super(EmbeddedAction, self).__init__(parent)
		self._actionObject = actionObject or None
		if not self._actionObject:
			print "no actionObject received for embedded action!"
			return
		self.name = self._actionObject.name
		# if isinstance(self._actionObject, ActionItem):
		# 	self.triggered.connect(self._actionObject.execute)
		# elif isinstance(self._actionObject, ActionList):
		# 	self.triggered.connect(self._actionObject.execute)
		self.triggered.connect(self._actionObject.execute)


class ContextMenu(object):
	"""this is no reason this doesn't inherit from qmenu now,
	but it already works fine"""

	def __init__(self, view, menu=None):
		self.view = view
		# self.rootMenu = menu or QtWidgets.QMenu("Take action:")
		self.rootMenu = QtWidgets.QMenu("Take action:")

	def exec_(self, pos):
		self.rootMenu.exec_(pos)

	#
	# def get_menu(self, name):
	# 	ctx_menu = self.view.context_menu()
	# 	root_menu = ctx_menu._menu_obj
	# 	for action in root_menu.actions():
	# 		if action.text() != name:
	# 			continue
	# 		menu = action.menu()
	# 		return ContextMenu(self.view, menu)

	def add_action(self, action):
		# action.setShortcutVisibleInContextMenu(True)
		self.rootMenu.addAction(action)

	def add_menu(self, name):
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

	def addSubAction(self, actionObject=None, parent=None):
		"""not robust at all but idgaf"""
		# regen bug affects this
		if not parent:
			parent = self.rootMenu
		# if isinstance(actionObject, ActionList):
		# 	for i in actionObject.getActions():
		# 		return self.addSubAction(i, parent=parent)
		# if actionObject.name == "clear Maya scene":
		# 	newAction = EmbeddedAction(actionObject=ActionItem({"func" : self.marker}),
		# 	                           parent=parent)
		# else:
		# 	newAction = EmbeddedAction(actionObject=actionObject, parent=parent)
		newAction = EmbeddedAction(actionObject=actionObject, parent=parent)
		newAction.setText(newAction.name)
		#print "addSubAction name is {}".format(newAction.name)
		parent.addAction(newAction)
		return newAction

	def marker(self):
		print "TRIGGERING ACTION"

	def add_command(self, name, func=None, shortcut=None, parent=None):
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

	def add_separator(self):
		self.rootMenu.addSeparator()

	def buildMenusFromDict(self, menuDict=None):
		"""updates context menu with any action passed to it
		"""
		self.rootMenu.addSeparator()
		try:
			#print "context menuDict is {}".format(menuDict)
			self.buildMenu(menuDict=menuDict, parent=self.rootMenu)
		except RuntimeError("SOMETHING WENT WRONG WITH CONTEXT MENU"):
			pass

	"""CONTEXT MENU ACTIONS for allowing procedural function execution"""

	def buildMenu(self, menuDict={}, parent=None):
		"""builds menu recursively from keys in dict
		currently expects actionItems as leaves"""
		# print ""
		for k, v in menuDict.iteritems():
			#print "k is {}, v is {}".format(k, v)
			if isinstance(v, dict):
				#print "buildMenu v is dict {}".format(v)
				if not v.keys():
				#	print "skipping"
					continue
				newParent = self.addSubMenu(name=k, parent=parent)
				self.buildMenu(v, parent=newParent)
			elif isinstance(v, list):
				#print "buildMenu v is list {}".format(v)
				for i in v:
					self.buildMenu(i, parent=parent)

			elif isinstance(v, ActionItem) or isinstance(v, ActionList)\
					or v.__class__.__name__ == "ActionItem":
				#print "buildMenu v is actionItem or actionList {} {}".format(v.name, v)
				# if not isinstance(v, ActionItem):
				# 	print "v dict is {}".format(pprint.pformat(v.__dict__))
				# else:
				# 	print "real v dict is {}".format(pprint.pformat(v.__dict__))
				if v._name == "clear Maya scene":
					# print "v dict is {}".format(pprint.pformat(v.__dict__))
					#v.items[0]() # works
					pass

				action = self.addSubAction(parent=parent, actionObject=v)
				# if v._name == "clear Maya scene":
				# 	action.triggered() # works
				#self.add_command(v.name, func=v.execute, parent=parent)

		pass

	def clearCustomEntries(self):
		"""clear only custom actions eventually -
		for now clear everything"""
		self.rootMenu.clear()
