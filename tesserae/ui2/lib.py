# reusable ui items
from PySide2 import QtWidgets, QtCore
from edRig.structures import ActionItem, ActionList
# from edRig.tesserae.jchan2.widgets.stylesheet import STYLE_QMENU
from edRig.tesserae.ui2.style import STYLE_QMENU
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as omui
import shiboken2, weakref
import maya.cmds as cmds
from shiboken2 import wrapInstance
import pprint

expandingPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Expanding,
	QtWidgets.QSizePolicy.Expanding,
)

vertExpandingPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Fixed,
	QtWidgets.QSizePolicy.Expanding,
)

horiExpandingPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Expanding,
	QtWidgets.QSizePolicy.Fixed,
)

staticPolicy = QtWidgets.QSizePolicy(
	QtWidgets.QSizePolicy.Fixed,
	QtWidgets.QSizePolicy.Fixed,
)

# https://github.com/mottosso/Qt.py by Marcus Ottosson

def getMayaWindow():
	pointer = omui.MQtUtil.mainWindow()
	return shiboken2.wrapInstance(long(pointer), QtWidgets.QWidget)

def getMayaMainWindow():
	pointer = omui.MQtUtil.mainWindow()
	return shiboken2.wrapInstance(long(pointer), QtWidgets.QMainWindow)


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



""" base class for uis in maya to avoid awful focus and event issues """
class KeyPressEater(QtCore.QObject):
	def eventFilter(self, obj, event):
		if event.type() == QtCore.QEvent.KeyPress:
			return True
		return QtCore.QObject.eventFilter(self, obj, event)


# class BaseMayaUi(QtWidgets.QDialog):
class BaseMayaUi(QtWidgets.QWidget):
	""" yep QDialogue looks weird to me too """
	def __init__(self, parent=None):
		super(BaseMayaUi, self).__init__(parent)
		self.setWindowFlags(QtCore.Qt.Window)
		self.eater = KeyPressEater(self) 
		self.installEventFilter( self.eater )

	def closeEvent(self, event):
		self.removeEventFilter(self.eater)
		return super(BaseMayaUi, self).closeEvent(event)



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


""" this entire action/embeddedAction/context system is AWFUL
convert to use abstractTree as base structure """


class EmbeddedAction(QtWidgets.QAction):
	"""the bridge between normal action items and qt"""

	def __init__(self, actionObject=None, parent=None):
		super(EmbeddedAction, self).__init__(parent)
		self._actionObject = actionObject or None
		if not self._actionObject:
			print "no actionObject received for embedded action!"
			return
		self.name = str(self._actionObject.name)
		self.triggered.connect(self._actionObject.execute)


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
			action = ActionItem(execDict={"func" : func})
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

	def addSubAction(self, actionObject=None, parent=None):
		"""not robust at all but idgaf"""
		# regen bug affects this
		if not parent:
			parent = self.rootMenu

		newAction = EmbeddedAction(actionObject=actionObject, parent=parent)
		newAction.setText(newAction.name)
		#print "addSubAction name is {}".format(newAction.name)
		parent.addAction(newAction)
		return newAction

	def marker(self):
		print "TRIGGERING ACTION"

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
			#print "context menuDict is {}".format(menuDict)
			self.buildMenu(menuDict=menuDict, parent=self.rootMenu)
		except RuntimeError("SOMETHING WENT WRONG WITH CONTEXT MENU"):
			pass

	"""CONTEXT MENU ACTIONS for allowing procedural function execution"""

	def buildMenu(self, menuDict=None, parent=None):
		"""builds menu recursively from keys in dict
		currently expects actionItems as leaves"""
		# print ""
		menuDict = menuDict or {}
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
				action = self.addSubAction(parent=parent, actionObject=v)


		pass

	def buildMenusFromTree(self, tree, parent=None):
		""" builds recursively from tree
		only actions at leaves are considered """
		if tree.branches: # add menu for multiple actions
			parent = self.addSubMenu(name=tree.name, parent=parent)
			for branch in tree.branches:
				self.buildMenusFromTree(branch, parent)
			return parent
		else: # add single entry for single action
			if not isinstance(tree.value, (ActionItem, ActionList)):
				return None
			action = self.addSubAction(tree.value, parent)




	def clearCustomEntries(self):
		"""clear only custom actions eventually -
		for now clear everything"""
		self.rootMenu.clear()


def event(msg=""):
	def decorate(f):
		def applicator(*args, **kwargs):
			try:
				f(*args, **kwargs)
			except:
				print(msg)
		return applicator
	return decorate