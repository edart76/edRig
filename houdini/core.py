
from edRig import hou
from edRig.lib import python
reload(python)


def returnNode(parent, node_type, node_name):
	""" returns node of name if it exists,
	or creates new node of type """
	if any(i.name() == node_name for i in parent.children()):
		return parent.node(node_name)
	return parent.createNode(node_type, node_name=node_name)

def getNetworkBox(parent, boxName):
	""" retrieves or creates network box"""
	box = parent.findNetworkBox(boxName)
	if not box:
		box = networkBoxFromComment(parent, boxName)
	if box is None:

		box = parent.createNetworkBox(boxName)
		box.setComment(boxName)
	return box

def networkBoxFromComment(parent, comment=""):
	boxes = parent.networkBoxes()
	if not boxes: return None
	for i in boxes:
		if i.comment() == comment:
			return i

def itemsInNetworkBox(parent, boxName="objects"):
	""" returns nodes contained in specified network box
	no checking yet for specific node types
	:type parent : hou.Node or hou.NetworkBox """
	if isinstance(parent, hou.NetworkBox):
		box = parent
	else:
		box = getNetworkBox(parent, boxName)
	return box.nodes(recurse=True)


def sortNodes(nodes):
	""" sorts nodes into alphabetical order, basic consistency
	across merges """
	nameMap = {node.name() : node for node in nodes}
	ordered = sorted(nameMap.keys())
	sortedNodes = list(nameMap.keys())
	for i, name in enumerate(ordered):
		sortedNodes[i] = nameMap[name]
	return sortedNodes

def checkIfMergesDirty(itemsToMerge, existingMerges):
	""" not trying to insert at index or anything, just simple
	check if merges need rebuilt """
	existingPaths = [i.parm("objpath1").evalAsString() for i in existingMerges]
	newPaths = [i.path() for i in itemsToMerge]
	if set(existingPaths) != set(newPaths): # any discrepancy?
		return True
	return False


def addPathParm(node, parmName="path", path=None):
	""" adds path to node, optionally populates it """

	parm = hou.StringParmTemplate(
		name=parmName, label=parmName, num_components=1,
		default_value=path, string_type=hou.stringParmType.NodeReference
	)
	parmGroup = node.parmTemplateGroup()
	parmGroup.addParmTemplate( parm )
	return parm


def populateMerge(targetMerge=None, items=None, singleObjMerge=False,
                  boxName="Merge_Objects", mergePrefix="merge",
                  transformIntoMerge=False):
	""" populates a single objmerge node with given list of items
	having multiple merge nodes looks cool, but alas it is too inconsistent
	and fragile
	:param target: either single objMerge if singleObjMerge,
		or normal merge node if you're cool and sexy
	:param mergePrefix: obj merges will be prepended this
	"""
	#merge = core.returnNode(parent, "merge", "merge_all")
	parent = targetMerge.parent()

	if singleObjMerge:
		targetMerge.setParms( { "numobj" : len(items)})
		for i, item in enumerate(items):
			targetMerge.setParms( {
				"objpath{}".format(i+1) : item.path(),
				#"xformtype" : transformIntoMerge
				"xformtype" : 1 # into this
			}) # look how boring this is
		return

	else:
		# find network box
		box = getNetworkBox(parent, boxName)

		if not checkIfMergesDirty(items, box.nodes()):
			# nothing changed, no action needed
			return

		for i in box.nodes():
			i.destroy()

		merges = []
		for i in items:
			objMerge = parent.createNode("object_merge", mergePrefix + "_" + i.name())
			objMerge.setParms( { "objpath1" : i.path(),
			                     "xformtype" : 1} )

			targetMerge.setNextInput( objMerge )
			box.addItem( objMerge )
			merges.append( objMerge )

		# set positions
		for i, val in enumerate(merges):
			val.moveToGoodPosition( relative_to_inputs=False )
		targetMerge.moveToGoodPosition( relative_to_inputs=True, move_outputs=True )

		box.fitAroundContents()


def makeMultiFileMerge(targetMerge=None, paths=None,
                  boxName=None, rootPath=None):
	""" no alternative this time - required to create separate node per file
	in paths, all feeding into single merge node
	"""

	""" PASSTHROUGH target merge at start and end of operation, or it will
	update each time """
	parent = targetMerge.parent()
	fileNodes = []

	targetMerge.bypass(1)

	# find network box
	box = getNetworkBox(parent, boxName)
	for i in box.nodes():
		i.destroy()

	rootPath = python.conformPathSeparators(rootPath)
	for path in paths:
		path = python.conformPathSeparators(path)
		#print(path.split(rootPath)[-1])
		nodeName = python.stripNonAlphaNumeric(
			path.split(rootPath)[-1]).split(".")[0]
		fileNode = parent.createNode("file", nodeName + "_file")
		try:
			fileNode.parm("file").set(path)
		except:
			print("could not set path {}".format(path))
			fileNode.destroy()
			continue
		fileNodes.append(fileNode)
		box.addItem(fileNode)
		# targetMerge.setNextInput( fileNode )
		fileNode.moveToGoodPosition()

		# set up group to add original path as group on geo
		groupNode = parent.createNode("group", nodeName+"_group")
		groupNode.parm("groupname").set(nodeName)
		groupNode.setInput(fileNode)
		box.addItem(groupNode)

		targetMerge.setNextInput(groupNode)


	targetMerge.moveToGoodPosition(move_outputs=True)
	box.fitAroundContents()
	targetMerge.bypass(0)

	return fileNodes

