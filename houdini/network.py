
""" General utilities for building and editing networks """
import os, sys, re, json
from edRig import hou

def getNetworkBox(parent, boxName, caseSensitive=False):
	""" retrieves or creates network box"""
	box = parent.findNetworkBox(boxName)
	if not box:
		box = networkBoxFromComment(parent, boxName, caseSensitive)
	if box is None:
		box = parent.createNetworkBox(boxName)
		box.setComment(boxName)
	return box

def networkBoxFromComment(parent, comment="", caseSensitive=False):
	"""Finds a network box in parent if it exists"""
	boxes = parent.networkBoxes()
	if not boxes: return None
	for i in boxes:
		if caseSensitive:
			if i.comment() == comment:
				return i
		else:
			if i.comment().lower() == comment.lower():
				return i
	return None

def itemsInNetworkBox(parent, boxName="objects", caseSensitive=False):
	""" returns nodes contained in specified network box
	no checking yet for specific node types
	:type parent : hou.Node or hou.NetworkBox """
	if isinstance(parent, hou.NetworkBox):
		box = parent
	else:
		box = getNetworkBox(parent, boxName, caseSensitive)
	return box.nodes(recurse=True)


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


def conformPathSeparators(line):
	""" ensures that any slash of any kind is os.path.separator"""
	return line.replace("\\", os.path.sep).replace("/", os.path.sep)

def stripNonAlphaNumeric(line, replace="_"):
	""" replaces all non-alphaNumeric characters with given item """
	return re.sub('[\W_]+', replace, line)

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

	rootPath = conformPathSeparators(rootPath)
	for path in paths:
		path = conformPathSeparators(path)
		#print(path.split(rootPath)[-1])
		nodeName = stripNonAlphaNumeric(
			path.split(rootPath)[-1]).split(".")[0]
		fileNode = parent.createNode("file", nodeName + "_file")
		try:
			fileNode.parm("file").set(path)
		except:
			print(("could not set path {}".format(path)))
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
