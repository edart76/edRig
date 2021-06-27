
import sys, os

global reload
try:
	reload = reload
except:
	from importlib import reload as rl
	reload = rl


from edRig import dcc
reload(dcc)


# import all the things
from edRig.dcc import ( hostDict,
	cmds, mel, om, oma, omui,
	hou, stateutils, objecttoolutils, hutil,
	bpy,
	hostDict,
	QtCore, QtWidgets, QtGui,
	unreal
    )

if hostDict["maya"]:

	from edRig.maya import AbsoluteNode, ECA, ECN
	from edRig.attr import con

sys.dont_write_bytecode = True
ROOT_PATH = "F:" + "/" + "all_projects_desktop" # root path of asset system
COMMON_PATH = ROOT_PATH + "/common"
CURRENT_PATH = os.path.dirname(os.path.realpath(__file__))
"""this asset system is designed to work with a central "common" folder,
containing rigging files like control shape libraries, any templates you want,
but also a common material library"""

# import site
# fp = r"C:\Users\Ed\AppData\Local\Programs\Python\Python37-32\Lib"
# #site.addsitedir(fp)
#
# sys.path.append(fp)

def log(message, **kwargs):
	print(message)

def reloadEdRig(tesserae=True):
	"""force reload all edRig packages
	if not tesserae, will try not to crash tesserae"""
	protecc = {"tesserae" : ("layers", "tesserae")}
	attacc = ("edRig", "tree")
	import sys
	for i in list(sys.modules.keys()):
		if any( n in i for n in attacc):
			del sys.modules[i]

""" STANDARDS
lol

"function" abbreviated to "fn" 
"create" used over "make" - "make" is ambigious: "make a cake" vs "make it go away"


"""

