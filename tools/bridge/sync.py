
"""
functions to call in any DCC scene, to bring it totally up to speed with the
wider ecosystem: reload references, export outputs, import inputs, everything
"""


from edRig import cmds, om, pipeline, scene
from edRig.node import AbsoluteNode, ECA, ObjectSet

from edRig import hou # it's happening


def sync():
	cmds.loadPlugin("objExport")
	pipeline.reloadAllReferences()

	path = pipeline.getScenePath()
	print("scenePath {}".format(path))
	if cmds.objExists("bridge_set"):
		syncBridgeSets()

def syncBridgeSets():
	topSet = ObjectSet("bridge_set")
	topSetItems = topSet.objects()
	print("topSetItems {}".format(topSetItems))

	# every set in a bridge set for now signifies an export
	for i in topSetItems:
		if i.nodeType() == "objectSet":
			#print(i)
			combineTargets = ObjectSet(i(), useCache=False).objects()
			# combine objects and export
			duplicates = [ cmds.duplicate(n, name=n+"_duplicate")[0] for n in combineTargets]

			combined = cmds.polyUnite(duplicates, ch=0, n=i.name+"_combined")

			# make bridge folder adjacent to scene
			parentDir = pipeline.FilePathTree(path).parent
			bridgeDir = parentDir.makeChildFolder("bridge")
			outputObjPath = bridgeDir + "/{}_mayaOutput.obj".format(i.name)

			pipeline.exportToObj(combined, outputObjPath)

			cmds.delete(combined)
			for n in duplicates:
				if cmds.objExists(n):
					cmds.delete(n)

			# add new namespace in anticipation

			scene.addNamespace("bridge_:{}_".format(i.name))
			# framestore readable underscore convention



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
			#print( "parmString is {}".format(mode)) # returns "read", "write"
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



