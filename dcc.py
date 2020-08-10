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

# host values
hostDict = {
	"maya" : False,
	"houdini" : False,
	"python" : False,
	"blender" : False
}

# running without ui
thisIsHeadless = False



# maya
try:
	from maya import cmds, mel
	import maya.api.OpenMaya as om
	import maya.api.OpenMayaAnim as oma
	import maya.api.OpenMayaUi as omui

	from edRig.node import AbsoluteNode, ECA
	from edRig.attr import con
	hostDict["maya"] = True
	pass
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



def getMaya():
	if not cmds:
		try:
			from maya import cmds, mel
			import maya.api.OpenMaya as om
			import maya.api.OpenMayaAnim as oma
			import maya.api.OpenMayaUi as omui
		except ImportError:
			print("this is not maya")

