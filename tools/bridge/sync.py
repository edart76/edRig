
"""
functions to call in any DCC scene, to bring it totally up to speed with the
wider ecosystem: reload references, export outputs, import inputs, everything
"""


from edRig import cmds, om, pipeline, scene
from edRig.node import AbsoluteNode, ECA, ObjectSet

def sync():
	cmds.loadPlugin("objExport")
	pipeline.reloadAllReferences()

	path = pipeline.getScenePath()
	print("scenePath {}".format(path))
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
