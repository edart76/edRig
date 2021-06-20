# reusable ui items
from edRig import QtWidgets, QtCore
#from edRig.structures import ActionItem, ActionList
from edRig.tesserae.action import Action
from edRig.tesserae.ui2.style import STYLE_QMENU
from edRig.lib.python import DataRef
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as omui
import shiboken2, weakref
import maya.cmds as cmds
from shiboken2 import wrapInstance
from functools import partial
import itertools
import pprint
import tree

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
	return shiboken2.wrapInstance(int(pointer), QtWidgets.QWidget)

def getMayaMainWindow():
	pointer = omui.MQtUtil.mainWindow()
	return shiboken2.wrapInstance(int(pointer), QtWidgets.QMainWindow)


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
	control_wrap = wrapInstance(int(control_widget), QtWidgets.QWidget)

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
		#self.installEventFilter( self.eater )

	def closeEvent(self, event):
		#self.removeEventFilter(self.eater)
		return super(BaseMayaUi, self).closeEvent(event)


class KeyState(object):
	""" holds variables telling if shift, LMB etc are held down
	currently requires events to update, may not be a good idea to
	query continuously """

	def __init__(self):
		self.LMB = DataRef(False)
		self.RMB = DataRef(False)
		self.MMB = DataRef(False)
		self.alt = DataRef(False)
		self.ctrl = DataRef(False)
		self.shift = DataRef(False)

		self.mouseMap = {
			self.LMB : QtCore.Qt.LeftButton,
			self.RMB : QtCore.Qt.RightButton,
			self.MMB : QtCore.Qt.MiddleButton }

		self.keyMap = {
			self.alt: QtCore.Qt.AltModifier,
			# self.ctrl: QtCore.Qt.ShiftModifier, ### w h y ###
			# self.shift: QtCore.Qt.ControlModifier, ### w h y ###
			self.ctrl: QtCore.Qt.ControlModifier,
			self.shift: QtCore.Qt.ShiftModifier,
		}
		# shift and ctrl are swapped for me I kid you not

	def mousePressed(self, event):
		for button, v in self.mouseMap.items():
			button( event.button() == v)
		self.syncModifiers(event)

	def mouseReleased(self, event):
		for button, v in self.mouseMap.items():
			if event.button() == v:
				button(False)
		self.syncModifiers(event)

	def keyPressed(self, event):
		self.syncModifiers(event)

	def syncModifiers(self, event):
		""" test each individual permutation of keys
		against event
		this is ridiculous """
		# keys = self.keyMap.keys()
		# for sequence in itertools.combinations_with_replacement(
		# 		keys, len(keys)):
		# 	val = self.keyMap[sequence[0]]
		# 	for key in sequence[1:]: # same values should collapse to single
		# 		val = val | self.keyMap[key]
		# 	if event.modifiers() == val:
		# 		for key in sequence:
		# 			key(True)
		# 		return
		# 	for key in sequence:
		# 		key(False)

		for key, v in self.keyMap.items():
			key((event.modifiers() == v)) # not iterable
		if event.modifiers() == (QtCore.Qt.ShiftModifier | QtCore.Qt.ControlModifier):
			self.ctrl(True)
			self.shift(True)


	def debug(self):
		print((self.mouseMap))
		print((self.keyMap))


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



def eventGuard(msg=""):
	def decorate(f):
		def applicator(*args, **kwargs):
			try:
				f(*args, **kwargs)
			except:
				print(msg)
		return applicator
	return decorate