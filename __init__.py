from __future__ import print_function
#from edRig.structures import EnvironmentSettings
import sys, os

cmds = None
om = None

try:
	from maya import cmds
	import maya.api.OpenMaya as om

	from edRig.node import AbsoluteNode, ECA
	from edRig.attr import con
	pass
except :
	print("this is not maya")
	pass

sys.dont_write_bytecode = True
ROOT_PATH = "F:" + "/" + "all_projects_desktop"
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

