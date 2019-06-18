"""interpreter-safe way of using houdini and maya in the same package"""

#### maya modules
cmds = None
om = None
oma = None
omui = None
mel = None

def getMaya():
	if not cmds:
		try:
			from maya import cmds, mel
			import maya.api.OpenMaya as om
			import maya.api.OpenMayaAnim as oma
			import maya.api.OpenMayaUi as omui
		except ImportError:
			print("this is not maya")


#### houdini module
hou = None