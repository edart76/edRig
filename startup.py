"""holds callback functions for when maya is opened or closed"""

from edRig.node import AbsoluteNode, ECA
from edRig import pipeline, attr
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
		#codeNode = AbsoluteNode("CodeNode")
		pass
	else:
		codeNode = ECA("network", name="CodeNode")
		# isPlaying attr
		attr.addAttr(codeNode, attrName="isPlaying", attrType="bool")
		# isTimeChanging attr
		attr.addAttr(codeNode, attrName="isTimeChanging", attrType="bool")
		# isScrubbing attr
		attr.addAttr(codeNode, attrName="isScrubbing", attrType="bool")

		# sub = ECA("pma", "CodeNodeSubtract", "-")
		# cmds.connectAttr(codeNode+".isTimeChanging", sub+".input1X")
		# cmds.connectAttr(codeNode+".isPlaying", sub+".input2X")
		# cmds.connectAttr(sub+".outputX", codeNode+".isScrubbing")
		# connectAttr doesn't work reliably at this stage of scene build


	# isPlaying
	conditions = ("playingBack", # this is scrubbing
	              "playingBackAuto",
	              "playblasting"
	              )
	def setIsPlaying(*args, **kwargs):
		# playingState = any(om.MConditionMessage.getConditionState(i)
		#                    for i in conditions)
		playingState = oma.MAnimControl.isPlaying()
		cmds.setAttr(codeNode+".isPlaying", playingState)
		pass
	# isTimeChanging
	def setIsTimeChanging(*args, **kwargs):
		changingState = (oma.MAnimControl.isPlaying() or
			oma.MAnimControl.isScrubbing())
		cmds.setAttr(codeNode+".isTimeChanging", changingState)
	#isScrubbing
	def setIsScrubbing(*args, **kwargs):
		changingState = oma.MAnimControl.isScrubbing()
		cmds.setAttr(codeNode+".isScrubbing", changingState)
	# for i in conditions:
	om.MDGMessage.addTimeChangeCallback(setIsPlaying)
	om.MDGMessage.addTimeChangeCallback(setIsTimeChanging)
	om.MDGMessage.addTimeChangeCallback(setIsScrubbing)
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
	om.MSceneMessage.addCheckCallback(
		om.MSceneMessage.kBeforeSaveCheck, beforeSaveCheck)
	om.MSceneMessage.addCheckCallback(
		om.MSceneMessage.kBeforeOpenCheck, beforeOpenCheck)

	om.MSceneMessage.addCallback(
		om.MSceneMessage.kAfterSave, afterSave)

	om.MSceneMessage.addCallback(
		om.MSceneMessage.kAfterOpen, afterOpen)

	om.MSceneMessage.addCallback(
		om.MSceneMessage.kBeforeNew, beforeNew)
	om.MSceneMessage.addCallback(
		om.MSceneMessage.kAfterNew, afterNew)

	setupViewport()
	pass

"""conditionNames:
(u'newing', u'playingBack', u'playingBackAuto', 
u'recording', u'deleteAllCondition', u'timeChangeTemp', 
u'SomethingSelected', u'autoKeyframeState', u'delete', 
u'deleteUndo', u'deleteRedo', u'isCurrentRenderLayerChanging', 
u'isApplyingMemberOverride', u'BatchMode', u'MayaInitialized', 
u'readingFile', u'ImageUIExists', u'BaseMayaExists', 
u'AnimationExists', u'PolyCoreExists', u'RenderingExists', 
u'BaseUIExists', u'flushingScene', u'GoButtonEnabled', 
u'ManipsExists', u'MayaCreatorExists', u'ModelExists', 
u'SubdivExists', u'PolygonsExists', u'PolyTextureExists', 
u'DynamicsExists', u'DatabaseUIExists', u'KinematicsExists', 
u'NurbsExists', u'DeformersExists', u'busy', u'UndoAvailable', 
u'RedoAvailable', u'opening', u'writingFile', u'postSceneCallbacks', 
u'readingReferenceFile', u'OpenMayaExists', u'alwaysWriteReferenced', 
u'playblasting', u'DimensionsExists', u'ClipEditorExists', u'AnimationUIExists', 
u'ModelUIExists', u'DynamicsUIExists', u'RenderingUIExists', u'ExplorerExists', 
u'PolygonsUIExists', u'DeformersUIExists', u'KinematicsUIExists', 
u'SubdivUIExists', u'NurbsUIExists', u'SurfaceUIExists', u'softSelectOptions', 
u'panZoomEnabled', u'playbackIconsCondition', u'hotkeyListChange', 
u'TimeEditorExists', u'nexHUDCondition')

	eventNames:
(u'dbTraceChanged', u'linearUnitChanged', u'timeUnitChanged', 
u'angularUnitChanged', u'Undo', u'undoSupressed', u'Redo', 
u'customEvaluatorChanged', u'serialExecutorFallback', u'timeChanged', 
u'currentContainerChange', u'quitApplication', u'idleHigh', u'idle', 
u'idleVeryLow', u'RecentCommandChanged', u'ToolChanged', u'PostToolChanged', 
u'ToolDirtyChanged', u'ToolSettingsChanged', u'tabletModeChanged', 
u'DisplayRGBColorChanged', u'animLayerRebuild', u'animLayerRefresh', 
u'animLayerAnimationChanged', u'animLayerLockChanged', u'animLayerBaseLockChanged', 
u'animLayerGhostChanged', u'cteEventKeyingTargetForClipChanged', 
u'cteEventKeyingTargetForLayerChanged', u'cteEventKeyingTargetForInvalidChanged', 
u'teClipAdded', u'teClipModified', u'teClipRemoved', u'teCompositionAdded', 
u'teCompositionRemoved', u'teCompositionActiveChanged', u'teCompositionNameChanged', 
u'teMuteChanged', u'cameraChange', u'cameraDisplayAttributesChange', 
u'SelectionChanged', u'PreSelectionChangedTriggered', u'LiveListChanged', 
u'ActiveViewChanged', u'SelectModeChanged', u'SelectTypeChanged', 
u'SelectPreferenceChanged', u'DisplayPreferenceChanged', u'DagObjectCreated',
 u'transformLockChange', u'renderLayerManagerChange', u'renderLayerChange', 
 u'displayLayerManagerChange', u'displayLayerAdded', u'displayLayerDeleted', 
 u'displayLayerVisibilityChanged', u'displayLayerChange', u'renderPassChange', 
 u'renderPassSetChange', u'renderPassSetMembershipChange', 
 u'passContributionMapChange', u'DisplayColorChanged', u'lightLinkingChanged',
u'lightLinkingChangedNonSG', u'UvTileProxyDirtyChangeTrigger', 
u'preferredRendererChanged', u'polyTopoSymmetryValidChanged', 
u'SceneSegmentChanged', u'PostSceneSegmentChanged', u'SequencerActiveShotChanged', 
u'ColorIndexChanged', u'deleteAll', u'NameChanged', 
u'symmetricModellingOptionsChanged', u'softSelectOptionsChanged', u'SetModified', 
u'xformConstraintOptionsChanged', u'metadataVisualStatusChanged', u'undoXformCmd',
 u'redoXformCmd', u'freezeOptionsChanged', u'linearToleranceChanged', 
 u'angularToleranceChanged', u'nurbsToPolygonsPrefsChanged', 
 u'nurbsCurveRebuildPrefsChanged', u'constructionHistoryChanged', 
 u'threadCountChanged', u'SceneSaved', u'NewSceneOpened', u'SceneOpened', 
u'SceneImported', u'PreFileNewOrOpened', u'PreFileNew', u'PreFileOpened', 
u'PostSceneRead', u'workspaceChanged', u'nurbsToSubdivPrefsChanged', 
u'PolyUVSetChanged', u'PolyUVSetDeleted', u'selectionConstraintsChanged', 
u'startColorPerVertexTool', u'stopColorPerVertexTool', u'start3dPaintTool', 
u'stop3dPaintTool', u'DragRelease', u'ModelPanelSetFocus', 
u'modelEditorChanged', u'MenuModeChanged', u'gridDisplayChanged', 
u'interactionStyleChanged', u'axisAtOriginChanged', u'CurveRGBColorChanged', 
u'SelectPriorityChanged', u'snapModeChanged', u'activeHandleChanged', 
u'ChannelBoxLabelSelected', u'texWindowEditorImageBaseColorChanged', 
u'texWindowEditorCheckerDensityChanged', u'texWindowEditorCheckerDisplayChanged', 
u'texWindowEditorDisplaySolidMapChanged', u'texWindowEditorShowup', 
u'texWindowEditorClose', u'colorMgtOCIORulesEnabledChanged', 
u'colorMgtUserPrefsChanged', u'RenderSetupSelectionChanged', 
u'colorMgtEnabledChanged', u'colorMgtConfigFileEnableChanged', 
u'colorMgtConfigFilePathChanged', u'colorMgtConfigChanged', 
u'colorMgtWorkingSpaceChanged', u'colorMgtPrefsViewTransformChanged', 
u'colorMgtPrefsReloaded', u'colorMgtOutputChanged', 
u'colorMgtPlayblastOutputChanged', u'colorMgtRefreshed', u'selectionPipelineChanged', 
u'playbackRangeChanged', u'playbackSpeedChanged', u'playbackModeChanged', 
u'playbackRangeSliderChanged', u'glFrameTrigger', u'currentSoundNodeChanged', 
u'graphEditorChanged', u'graphEditorParamCurveSelected', 
u'graphEditorOutlinerHighlightChanged', u'graphEditorOutlinerListChanged', 
u'EditModeChanged', u'RenderViewCameraChanged', u'texScaleContextOptionsChanged', 
u'texRotateContextOptionsChanged', u'texMoveContextOptionsChanged', 
u'polyCutUVSteadyStrokeChanged', u'polyCutUVEventTexEditorCheckerDisplayChanged', 
u'polyCutUVShowTextureBordersChanged', u'polyCutUVShowUVShellColoringChanged', 
u'shapeEditorTreeviewSelectionChanged', u'poseEditorTreeviewSelectionChanged',
 u'sculptMeshCacheBlendShapeListChanged', u'sculptMeshCacheCloneSourceChanged', 
u'RebuildUIValues', u'cteEventClipEditModeChanged', u'teEditorPrefsChanged')
"""
