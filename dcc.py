"""interpreter-safe way of using houdini and maya in the same package"""

#### maya modules
cmds = None
om = None
oma = None
omui = None
mel = None


#### houdini module
hou = None


# host values
thisIsMaya = False
thisIsHoudini = False
thisIsPython = False

# running without ui
thisIsHeadless = False




try:
	from maya import cmds, mel
	import maya.api.OpenMaya as om
	import maya.api.OpenMayaAnim as oma
	import maya.api.OpenMayaUi as omui

	from edRig.node import AbsoluteNode, ECA
	from edRig.attr import con
	thisIsMaya = True
	pass
except :
	#print("this is not maya")
	pass

# houdini setup
try:
	import hou
	#print("omg this is houdini")
	thisIsHoudini = True
except:
	pass

# this mechanism seems to work well



def getMaya():
	if not cmds:
		try:
			from maya import cmds, mel
			import maya.api.OpenMaya as om
			import maya.api.OpenMayaAnim as oma
			import maya.api.OpenMayaUi as omui
		except ImportError:
			print("this is not maya")

