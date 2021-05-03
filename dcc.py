"""interpreter-safe way of using houdini and maya in the same package"""

#### maya modules
cmds = None
om = None
oma = None
omui = None
mel = None


#### houdini modules
hou = None
hutil = None
stateutils = None
objecttoolutils = None

#### blender modules
bpy = None # are there any others that matter

#### pyside modules, it's convenient to use the same system
QtCore = None
QtWidgets = None
QtGui = None

#### unreal modules
unreal = None # there can be only one


# host values
hostDict = {
	"maya" : False,
	"houdini" : False,
	"python" : False,
	"blender" : False,
	"unreal" : False
}

# host exes
exeMap = {
	"maya" : "",
	"houdini" : "C:\Program Files\Side Effects Software\Houdini 18.0.287\bin\happrentice.exe",
}

# running without ui
thisIsHeadless = False
qtAvailable = False

# maya
try:
	from maya import cmds, mel
	import maya.api.OpenMaya as om
	import maya.api.OpenMayaAnim as oma
	import maya.api.OpenMayaUI as omui

	hostDict["maya"] = True

	from functools import wraps
	import traceback
	# patch maya cmds "list-" functions to return lists no matter what
	listFunctions = ["ls", "listRelatives", "listHistory", "listConnections",
	                 "listAttr"]

	def returnList(wrapFn):
		@wraps(wrapFn)
		def _innerFn(*args, **kwargs):
			result = wrapFn(*args, **kwargs)
			if result is None:
				print("returned None, changing to list")
				return []
			return result
		return _innerFn

	for fnName in listFunctions:
		try:
			fn = getattr(cmds, fnName)
			setattr(cmds, fnName, returnList(fn))
		except:
			print("error wrapping {}".format(fn.__name__))
			print(traceback.format_exc())


except Exception as e:
	pass

# houdini
try:
	import hou, stateutils, objecttoolutils, hutil
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

# unreal
try:
	import unreal # there can be only one
	hostDict["unreal"] = True
except:
	pass