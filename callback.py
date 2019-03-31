"""wrappers for OpenMaya callbacks"""
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from edRig import core

def addCallbackOnPlugChanged(listenPlug, callbackFn=None):
	"""executes callbackFn when listenPlug is changed by user
	WILL NOT BE CALLED DURING PLAYBACK - this is only active for the
	user's direct interaction
	:param listenPlug : string name of plug"""
	event = om.MNodeMessage.kAttributeEval
	# event = om.MNodeMessage.kAttributeSet
