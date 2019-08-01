"""wrappers for OpenMaya callbacks"""
from maya import cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
from edRig import core


class RegenCallback(object):
	"""decorator class to add callbacks to the global scriptNode,
	ensuring they are regenerated on maya scene open"""

	def __init__(self, *args, **kwargs):
		pass

	def __call__(self, *args, **kwargs):
		pass

class CallbackObject(object):
	"""potentially necessary if we can't figure out proper arguments"""

def addCallbackOnPlugChanged(listenPlug, callbackFn=None):
	"""executes callbackFn when listenPlug is changed by user
	WILL NOT BE CALLED DURING PLAYBACK - this is only active for the
	user's direct interaction
	:param listenPlug : string name of plug to attach callback
	:param callbackFn : function to trigger, passed plug name as argument"""
	event = om.MNodeMessage.kAttributeEval
	tokens = listenPlug.split(".")
	nodeObj = getMObject(tokens[0])

	def callbackHandler(*args, **kwargs):
		""" receives ( eventConstant, mPlug, dummy mPlug, clientData)
		TO DO optimise by maintaining single callback
		and dict of plug : function"""
		print "event id {}".format(args[0])
		print args[1].name()
		# print args[2].name() # none usually
		if args[1].name() == listenPlug:
			callbackFn()

	# event = om.MNodeMessage.kAttributeSet
	id = om.MNodeMessage.addAttributeChangedCallback(
		nodeObj, callbackHandler)
	return id


def addTimeChangedCallback(callbackFn):
	id = om.MDGMessage.addTimeChangeCallback(callbackFn)
	return id

def getMObject(node):
	sel = om.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)



