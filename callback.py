"""wrappers for OpenMaya callbacks"""
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma


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
		#print "event id {}".format(args[0])
		#print args[1].name()
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

