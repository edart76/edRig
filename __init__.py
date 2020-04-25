from __future__ import print_function
#from edRig.structures import EnvironmentSettings
import sys, os

# maya modules
#cmds = None
#om = None

# houdini modules
#hou = None

# maya setup
try:
	from maya import cmds
	import maya.api.OpenMaya as om

	from edRig.node import AbsoluteNode, ECA
	from edRig.attr import con
	thisIsMaya = True
	pass
except :
	# this is not maya
	# this system definitely works
	pass

# # houdini setup
# try:
# 	from houdini import hou
# 	print("omg this is houdini")
# 	thisIsHoudini = True
# except:
# 	pass

# import all the things
from edRig.dcc import cmds, mel, om, oma, omui, \
	hou, stateutils, objecttoolutils


sys.dont_write_bytecode = True
ROOT_PATH = "F:" + "/" + "all_projects_desktop" # root path of asset system
COMMON_PATH = "F:" + "/" + "all_projects_desktop/common"
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
"""this asset system is designed to work with a central "common" folder,
containing rigging files like control shape libraries, any templates you want,
but also a common material library"""


def log(message, **kwargs):
	print(message)

""" STANDARDS
lol

"function" abbreviated to "fn" 


"""

