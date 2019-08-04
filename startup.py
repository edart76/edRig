"""holds callback functions for when maya is opened or closed"""

from edRig.node import AbsoluteNode, ECA
from edRig import pipeline, attr, callback
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.OpenMaya as omOld # the things we do for rigging
from maya import cmds
import os

"""the objective: remove the student warning every time you breathe on maya
    i'm already poor, i don't need reminding every second of the day

	the method: when a file is opened, the flag must be gone
		when a file is saved, the flag must be there
		
	beforeSaving: add the flag. afterSaving: remove the flag"""

def clearCallbacks():
	pass

def callbackDelayed(*args, **kwargs):
	#print "callbackDelayed" works
	cmds.createNode("transform", n="delayedTest")

def makeCodeNode():
	"""creates or returns a network node containing useful information about scene,
	updated by callback. run at initialisation and scene open"""
	# current playback range
	# is playing
	# is scrubbing
	codeNode = None
	if cmds.objExists("CodeNode"):
		codeNode = AbsoluteNode("CodeNode")
		return

	codeNode = ECA("network", name="CodeNode")

	attr.addAttr(codeNode, attrName="isPlaying", attrType="bool")
	attr.addAttr(codeNode, attrName="isTimeChanging", attrType="bool")
	attr.addAttr(codeNode, attrName="isScrubbing", attrType="bool")

	# attr to toggle live playback
	attr.addAttr(codeNode, attrName="livePlayback", attrType="bool",
	             keyable=True )
	attr.addAttr(codeNode, attrName="liveCallbackId", attrType="string",
	             keyable=False )
	attr.addAttr(codeNode, attrName="liveTime", attrType="long", dv=1,
	             keyable=True)

	# plug for tracking solvers
	attr.addAttr(codeNode, attrName="solvers", attrType="message")
	attr.addAttr(codeNode, attrName="dt", attrType="float")

	# get plugs for faster updates
	playingPlug = codeNode.getMPlug("isPlaying")
	timeChangingPlug = codeNode.getMPlug("isTimeChanging")
	scrubbingPlug = codeNode.getMPlug("isScrubbing")
	livePlug = codeNode.getMPlug("livePlayback")
	liveIdPlug = codeNode.getMPlug("liveCallbackId")
	liveTimePlug = codeNode.getMPlug("liveTime")
	solverPlug = codeNode.getMPlug("solvers")
	dtPlug = codeNode.getMPlug("dt")




	def setIsPlaying(*args, **kwargs):
		playingState = oma.MAnimControl.isPlaying()
		#cmds.setAttr(codeNode+".isPlaying", playingState)
		playingPlug.setBool(playingState)
		pass
	# isTimeChanging
	def setIsTimeChanging(*args, **kwargs):
		changingState = (oma.MAnimControl.isPlaying() or
			oma.MAnimControl.isScrubbing())
		#cmds.setAttr(codeNode+".isTimeChanging", changingState)
		timeChangingPlug.setBool(changingState)
	#isScrubbing
	def setIsScrubbing(*args, **kwargs):
		changingState = oma.MAnimControl.isScrubbing()
		#cmds.setAttr(codeNode+".isScrubbing", changingState)
		scrubbingPlug.setBool(changingState)

	def updateCodeNode(*args, **kwargs):
		"""place all updates in a single callback"""
		setIsPlaying()
		setIsTimeChanging()
		setIsScrubbing()

	updateId = om.MDGMessage.addTimeChangeCallback(updateCodeNode)

	def updatePlaybackPlug(*args, **kwargs):
		"""called when playbackPlug is manually changed"""
		state = livePlug.asBool()
		currentId = int(liveIdPlug.asString() or "0")
		if state:
			# do we already have an id active?
			if currentId:	pass
			else:	addLiveCallback(codeNode)
		else:
			removeLiveCallback(codeNode)
		print state

	def addLiveCallback(node, timeStep=0.1):
		liveTimePlug.setInt(1)
		id = om.MTimerMessage.addTimerCallback(
			timeStep, incrementLiveTime)
		# node.set("liveCallbackId", id)
		liveIdPlug.setString(str(id))
		pass

	def removeLiveCallback(node):
		id = int(liveIdPlug.asString() or "0")
		if not id:
			return
		om.MTimerMessage.removeCallback(id)
		liveIdPlug.setString("0")
		pass

	def incrementLiveTime(*args, **kwargs):
		"""this is main function called to update solvers, dynamics etc
		called as part of mTimerMessage
		passed: ( time since last running in seconds,
			time taken to execute in seconds,
			userData)"""
		print "args {}".format(args)
		liveTimePlug.setInt( liveTimePlug.asInt() + 1)
		dtPlug.setFloat( args[0] )

	def overrideLiveTime(*args, **kwargs):
		"""override live time when actual playback begins"""
		removeLiveCallback(codeNode)

	# print "condition args {}".format(args)
	liveId = callback.addCallbackOnPlugChanged(
		codeNode+".livePlayback", updatePlaybackPlug)
	overrideId = om.MConditionMessage.addConditionCallback(
		"playingBack", overrideLiveTime)



	# for i in conditions:
	# om.MDGMessage.addTimeChangeCallback(setIsPlaying)
	# om.MDGMessage.addTimeChangeCallback(setIsTimeChanging)
	# om.MDGMessage.addTimeChangeCallback(setIsScrubbing)
	# this modest amount of callbacks gives 315 fps in an empty scene
	# i think we'll be fine





def afterSave(*args, **kwargs):
	print
	print "afterSave args are {}".format(args)
	print "afterSave kwargs are {}".format(kwargs)
	sceneName = cmds.file(q=True, sceneName=True)
	print "sceneName is {}".format(sceneName)
	#cmds.evalDeferred("import edRig;edRig.pipeline.makeLegit('"+sceneName+"')", lp=True)
	pipeline.makeLegit(sceneName)

def afterOpen(*args, **kwargs):
	sceneName = cmds.file(q=True, sceneName=True)
	clearCallbacks()
	print "sceneName is " + sceneName
	#pipeline.makeBogus(sceneName)
	makeCodeNode()

def afterNew(*args, **kwargs):
	makeCodeNode()




def beforeSaveCheck(*args, **kwargs):
	print
	toBeSaved = omOld.MFileIO.beforeSaveFilename()
	print "toBeSaved is " + toBeSaved

	return True

def beforeOpenCheck(*args, **kwargs):
	toBeOpened = omOld.MFileIO.beforeOpenFilename()
	print "toBeOpened is " + toBeOpened

	return True


def beforeNew(*args, **kwargs):
	"""are you SURE you don't want to save changes to that empty scene?
	like but are you SURE though"""
	# modified = cmds.file(q=True, modified=True)
	# if not modified:
	# 	cmds.file(new=True, force=True)

def setupViewport():
	"""makes things silky smooth"""
	cmds.setAttr("hardwareRenderingGlobals.transparentShadow", 1)
	cmds.setAttr( "hardwareRenderingGlobals.ssaoSamples", 8)
	cmds.setAttr( "hardwareRenderingGlobals.lineAAEnable", 1)

def mainStartup():
	# ECA("transform", name="mainStartup")
	# om.MSceneMessage.addStringArrayCallback(
	# 	om.MSceneMessage.kAfterPluginLoad, callbackDelayed) # works
	# om.MSceneMessage.addCheckCallback(
	# 	om.MSceneMessage.kBeforeSaveCheck, beforeSaveCheck)
	# om.MSceneMessage.addCheckCallback(
	# 	om.MSceneMessage.kBeforeOpenCheck, beforeOpenCheck)
	#
	# om.MSceneMessage.addCallback(
	# 	om.MSceneMessage.kAfterSave, afterSave)
	#
	# om.MSceneMessage.addCallback(
	# 	om.MSceneMessage.kAfterOpen, afterOpen)
	#
	# om.MSceneMessage.addCallback(
	# 	om.MSceneMessage.kBeforeNew, beforeNew)
	# om.MSceneMessage.addCallback(
	# 	om.MSceneMessage.kAfterNew, afterNew)

	setupViewport()
	pass
