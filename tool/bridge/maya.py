
""" maya-facing sync functions """

from edRig import cmds, om, pipeline, scene
import importlib
importlib.reload(pipeline)
importlib.reload(scene)
from edRig.node import AbsoluteNode, ECA, ObjectSet

from edRig.core import debug


def toolClick():
	""" entrypoint for the single maya sync button """
	sync()

def setupBridgeSets():
	bridge = ObjectSet.create("bridge_set")
	importSet = ObjectSet.create("import_set")
	exportSet = ObjectSet.create("export_set")
	bridge.addToSet(importSet)
	bridge.addToSet(exportSet)
	return bridge


def getBridgeSet():
	""" creates basic bridge sets for scene """
	if not cmds.objExists("bridge_set"):
		print("bridge set not found, creating")
		return setupBridgeSets()
	return ObjectSet("bridge_set")


def sync():
	""" maya facing sync """
	cmds.loadPlugin("objExport")
	pipeline.reloadAllReferences()

	path = pipeline.getScenePath()
	#print("scenePath {}".format(path))
	syncBridgeSets()

def syncBridgeSets():
	""" sync bridge sets found in maya scene """
	topSet = getBridgeSet()
	exportSet = ObjectSet("export_set")
	exportSetItems = exportSet.objects()
	print(("topSetItems {}".format(exportSetItems)))

	path = pipeline.getScenePath()

	# every set in a bridge set for now signifies an export
	for i in exportSetItems:

		# if subset is specified, all contained objects are combined
		if i.nodeType() == "objectSet":
			#print(i)
			combineTargets = ObjectSet(i(), useCache=False).objects()
			# combine objects and export
			duplicates = [ cmds.duplicate(n, name=n+"_duplicate")[0] for n in combineTargets]

		else: # export every top-level mesh in main export set individually
			duplicates = cmds.duplicate(i, name=i + "_duplicate")

		for n in duplicates:
			prepSyncGeo(n)

		# make bridge folder adjacent to scene
		parentDir = pipeline.FilePathTree(path).parent
		bridgeDir = parentDir.makeChildFolder("bridge")
		outputObjPath = bridgeDir + "/{}_mayaOutput.obj".format(i.name)
		outputFbxPath = bridgeDir + "/{}_mayaOutput.fbx".format(i.name)
		outputAbcPath = bridgeDir + "/{}_mayaOutput.abc".format(i.name)

		#pipeline.exportToObj(duplicates, outputObjPath)
		pipeline.exportToFbx(duplicates, outputFbxPath)
		#pipeline.exportToAlembic(duplicates, outputAbcPath)

		#cmds.delete(combined)
		for n in duplicates:
			if cmds.objExists(n):
				cmds.delete(n)

		# add new namespace in anticipation

		# scene.addNamespace("bridge_:{}_".format(i.name))
		# framestore readable underscore convention

def prepSyncGeo(geo):
	""" run any passes needed for geometry to pass through bridge properly """
	# fbx does weird stuff with linear nurbs curves
	# resample densely to a higher degree

	if cmds.nodeType(geo) == "nurbsCurve" or cmds.nodeType(geo+"Shape") == "nurbsCurve":
		if cmds.getAttr( geo + ".degree" ) == 1:
			cmds.rebuildCurve( geo, fitRebuild=0,
			                   rebuildType=0, #uniform
			                   spans=100,
			                   degree=3,
			                   ch=0
			                   )

	pass