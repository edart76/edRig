"""wrappers for OpenMaya callbacks"""
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from edRig import core
from edRig.scene import Globals

class RegenCallback(object):
	"""decorator class to add callbacks to the global scriptNode,
	ensuring they are regenerated on maya scene open"""

	def __init__(self, *args, **kwargs):
		pass

	def __call__(self, *args, **kwargs):
		pass

def addCallbackOnPlugChanged(listenPlug, callbackFn=None):
	"""executes callbackFn when listenPlug is changed by user
	WILL NOT BE CALLED DURING PLAYBACK - this is only active for the
	user's direct interaction
	:param listenPlug : string name of plug"""
	event = om.MNodeMessage.kAttributeEval
	# event = om.MNodeMessage.kAttributeSet
