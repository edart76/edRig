
"""
functions to call in any DCC scene, to bring it totally up to speed with the
wider ecosystem: reload references, export outputs, import inputs, everything
"""

sdsffsaawad
from edRig import cmds, om, pipeline, scene
from edRig.node import AbsoluteNode, ECA, ObjectSet

from edRig import hou # it's happening
from edRig.core import debug

def getBridgeSet():
	""" creates basic bridge sets for scene """
	if not cmds.objExists("bridge_set"):
		print("bridge set not found, creating")
		return ObjectSet.create("bridge_set")
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
	topSetItems = topSet.objects()
	print("topSetItems {}".format(topSetItems))

	path = pipeline.getScenePath()

	# every set in a bridge set for now signifies an export
	for i in topSetItems:

		debug(i)

		if i.nodeType() == "objectSet":
			#print(i)
			combineTargets = ObjectSet(i(), useCache=False).objects()
			# combine objects and export
			duplicates = [ cmds.duplicate(n, name=n+"_duplicate")[0] for n in combineTargets]

		else: # one export for every top-level model in the set
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

		scene.addNamespace("bridge_:{}_".format(i.name))
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



def syncHIO():
	syncHInputs()
	syncHOutputs()

def syncHInputs():
	""" begins from root obj node - recurses through all nodes for now
	when file node is found in load mode, reloads geometry """
	root = hou.node("/")
	for i in root.allSubChildren():
		#print("node {}, node type {}".format(i, i.type()))
		if i.type().name() == "file":
			#print("found file {}".format(i))
			button = i.parm( "reload" )
			mode = i.parm( "filemode" ).evalAsString()
			# returns "read", "write"
			# if you leave file nodes on auto you're an animal and i have no sympathy
			if mode == "read":
				button.pressButton()

def syncHOutputs(onlyHDA=True):
	""" looks for files or for specific export HDAs"""
	root = hou.node("/")
	for i in root.allSubChildren():
		if i.type().name() == "Ed_export_geo":
			button = i.parm( "stashinput" )
			button.pressButton()
	""" I wrote this HDA having absolutely no perspective on the coding side - 
	node and attribute names may certainly change in future """



