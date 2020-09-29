"""interpreter-safe way of using houdini and maya in the same package"""

#### maya modules
cmds = None
om = None
oma = None
omui = None
mel = None


#### houdini modules
hou = None
stateutils = None
objecttoolutils = None

#### blender modules
bpy = None # are there any others that matter

#### pyside modules, it's convenient to use the same system
QtCore = None
QtWidgets = None
QtGui = None


# host values
hostDict = {
	"maya" : False,
	"houdini" : False,
	"python" : False,
	"blender" : False
}

# running without ui
thisIsHeadless = False
qtAvailable = False

# maya
try:
	from maya import cmds, mel
	import maya.api.OpenMaya as om
	import maya.api.OpenMayaAnim as oma
	import maya.api.OpenMayaUi as omui

	from edRig.node import AbsoluteNode, ECA
	from edRig.attr import con
	hostDict["maya"] = True

	from functools import wraps
	# patch maya cmds "list-" functions to return lists no matter what
	listFunctions = ["ls", "listRelatives", "listHistory", "listConnections"]

	def returnList(fn):
		@wraps(fn)
		def _innerFn(*args, **kwargs):
			result = fn(*args, **kwargs)
			if result is None:
				return []
			return result
		return _innerFn

	for fnName in listFunctions:
		fn = getattr(cmds, fnName)
		setattr(cmds, fnName, returnList(fn))


except :
	pass

# houdini
try:
	import hou, stateutils, objecttoolutils
	#print("omg this is houdini")
	hostDict["houdini"] = True
except:
	pass

# blender
try:
	import bpy
	#print("hoots mon he's away doon the blender")
	hostDict["blender"] = True
except:
	pass
# this mechanism seems to work well

# qt / pyside2
try:
	from PySide2 import QtCore, QtWidgets, QtGui
	qtAvailable = True
except:
	pass