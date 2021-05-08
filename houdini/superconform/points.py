
""" fully aware that the code below is not elegant,
I had a bit of trouble figuring this out """


from collections import defaultdict
import json
from six import string_types, iteritems

from edRig import hou
from edRig.houdini import network, parm, core
import importlib
importlib.reload(core)
importlib.reload(network)

# node types in houdini are so weird
conformNodeTypeNames = ("null", )
conformNodeTypes = [hou.objNodeTypeCategory().nodeType(i)
                    for i in conformNodeTypeNames]

def gatherTopoPoints(
		topoSubnet
):
	"""Gather and sort master points on the topology
	mesh
	we look for specific "MIRROR" and "IGNORE" network boxes
	return dict of {"single" : nodes, "mirror" : nodes}
	 :param topoSubnet : hou.Node"""

	topoChildren = core.sortNodes(topoSubnet.children())
	# filter only null nodes
	topoChildren = list([x for x in topoChildren if (x.type() in conformNodeTypes)])

	# check for mirror membership
	mirrorBox = network.getNetworkBox(topoSubnet, "MIRROR")
	mirrorItems = set(network.itemsInNetworkBox(mirrorBox))
	# only nulls
	mirrorItems.intersection_update(set(topoChildren))
	single = set(topoChildren) - set(mirrorItems)

	# mirrored topo point creates two shape points,
	# but one created point will be mirrored by default

	return {"single" : list(single), "mirror" : list(mirrorItems)}

def validateTopoPointNaming(node, isMirror=False):
	"""check naming of topo point nodes - singles are given "C_" if
	not otherwise defined
	Mirrored nodes are L by default"""
	sides = "LRC"
	# for node in singleNodes:
	if not (node.name()[1] == "_" and node.name()[0].upper() in sides):
		char = "L" if isMirror else "C"
		node.setName(char + "_" + node.name())
	elif not node.name()[0].isupper(): # enforce upper case
		node.setName(node.name()[0].upper() + node.name()[1:])


# path connections are used to make system robust to renaming
"""Mirrored topo points map to 2 separate shape points on creation - 
if one of those is placed in Mirror field, 2nd shape point disappears"""

folderLabel = "Connected Points"
folderName = "pointfolder"
parmLabel = "Point"
parmName = "pointop"
def addPointPathConnections(point, nConnections=1):
	""" ensure that each topo point has one or two path parametres
	pointing to its corresponding shape points """


	group = point.parmTemplateGroup()
	# set number of connections
	folderTemplate = hou.FolderParmTemplate(
		folderName, folderLabel,
		folder_type=hou.folderType.ScrollingMultiparmBlock,
		default_value=nConnections,
	    ends_tab_group=False)
	pathTemplate = hou.StringParmTemplate(parmName + "#", parmLabel, 1,
		string_type=hou.stringParmType.NodeReference)
	pathTemplate.setTags({"opfilter": "!!OBJ/NULL!!", "oprelative": ".", "script_callback_language": "python"})
	folderTemplate.addParmTemplate(pathTemplate)
	group.append(folderTemplate)
	# point.setParmTemplateGroup(group)

	point.setParmTemplateGroup(group)

def getPointPathParms(point):
	"""retrieve individual path parametres from point"""
	result = []  # return connection parametres
	for param in point.parms():
		if param.isMultiParmInstance():
			result.append(param)
	return result

def checkPointParms(point, nConnections=2):
	""" check that conform point has expected connections
	APPARENTLY multiparm folders are no longer folders,
	they're just normal parametres
	return sequence of connection params in order
	"""
	group = point.parmTemplateGroup()
	if not group.find(folderName):
		addPointPathConnections(point, nConnections)
	# check path value
	return getPointPathParms(point)

def addShapePoint(topoPoint, shapeSubnet, name=None):
	""""generate shape point"""
	name = name or topoPoint.name()
	newNode = shapeSubnet.createNode("null", node_name=name)
	param = checkPointParms(newNode, 1)[0]
	param.set(topoPoint.path())

	# move to same position
	newNode.setPosition(topoPoint.position())

	return newNode

"""
for every topo point node:
check that it has required attributes - if not create them
check that attributes are linked properly to shape points
if not:
	look for shape points with matching names. 
	if found, link them
	if not:
		create them, add path attributes, link them
"""

def pointProcessMain(topoSubnet, topoMerge,
                     shapeSubnet, shapeMerge,
                     data=None):
	""" main function run by superconform point processing
	:param data: any random data needed """

	prevTopoPaths = data.get("prevTopoNodes") or []
	#print("prevPaths", prevTopoPaths)
	prevTopoNodes = [hou.node(i) for i in prevTopoPaths]

	topoPoints = gatherTopoPoints(topoSubnet)
	for point in topoPoints["single"]:
		validateTopoPointNaming(point)
	for point in topoPoints["mirror"]:
		validateTopoPointNaming(point, isMirror=True)
	allTopoPoints = topoPoints["single"] + topoPoints["mirror"]

	shapePoints = gatherTopoPoints(shapeSubnet)
	topoBox = network.getNetworkBox(topoSubnet, "MIRROR")

	# reset connections on new topo points
	newTopoPoints = [i for i in allTopoPoints if not i in prevTopoNodes]
	#print("prev", prevTopoNodes)
	print(("new", newTopoPoints))
	for newPoint in newTopoPoints:
		parms = getPointPathParms(newPoint)
		for i in parms:
			i.set("")


	# check mirror box:
	shapeBox = network.getNetworkBox(shapeSubnet, "MIRROR")
	shapeBox.setColor(hou.Color((0.5, 0.6, 0.8)))


	topoShapeMap = {}
	shapeTopoMap = {} # individual shape point to driver topo point
	# can be bijective
	shapeMirrorMap = {} # not used yet

	for topoPoint in allTopoPoints:
		nConnections = 1 if topoPoint.name()[0].lower() == "c" else 2
		params = checkPointParms(topoPoint, nConnections)

		# check connections
		# if topo point params are empty:
			# check shape points by name
			# if matching name found:
				# populate topo point connections
			# else:
				# create new shape point(s) based on mirror status of topo
				# link to topo

		# if TOPO is in mirror but SHAPE is not (has been moved out of it)
		# create corresponding SHAPE point
		# if SHAPE is in mirror, ignore any corresponding SHAPE points

		# form map of {topo point : shape points}
		found = [i.evalAsNode() for i in params if i.evalAsNode()]
		print(("found", found))
		if not found:
			# check if matching node exists
			if shapeSubnet.node(topoPoint.name()):
				shapePoint = shapeSubnet.node(topoPoint.name())
			else:
				# create shape points
				shapePoint = topoPoint.copyTo(shapeSubnet)
			params[0].set(shapePoint.path())
			found = [shapePoint]
			if topoPoint in topoPoints["mirror"]:
				shapeBox.addItem(shapePoint)
				shapePoints["mirror"].append(shapePoint)
			else:
				shapePoints["single"].append(shapePoint)

		if len(found) == 1: # match name exactly
			print("len 1")
			found[0].setName(topoPoint.name())
		elif len(found) == 2: # one point mapping to 2
			print("len2")
			found[0].setName("L" + topoPoint.name()[1:])
			found[1].setName("R" + topoPoint.name()[1:])

		topoShapeMap[topoPoint] = found
		for shapePoint in found:
			shapeTopoMap[shapePoint] = topoPoint

	shapeBox.fitAroundContents()
	shapePoints["mirror"] = list(set(shapePoints["mirror"]))
	shapePoints["single"] = list(set(shapePoints["single"]))

	# merge geometries

	topoOrdered = sorted(allTopoPoints, key=lambda x : x.name())
	populateMerge(topoMerge, topoOrdered)

	allShapePoints = shapePoints["single"] + shapePoints["mirror"]

	shapeOrdered = sorted(allShapePoints, key=lambda x : x.name())
	populateMerge(shapeMerge, shapeOrdered)

	for topoPoint, linkPoints in iteritems(topoShapeMap):
		for shapePoint in linkPoints:
			shapePoint.setPosition(topoPoint.position())


	# get mirror group indices
	topoMirrorIndices = [topoOrdered.index(i) for i in topoPoints["mirror"]]
	shapeMirrorIndices = [shapeOrdered.index(i) for i in shapePoints["mirror"]]



	# output values
	return {
		"allTopo" : topoOrdered,
		"mirrorTopo" : [i for i in topoOrdered
		                if i in topoPoints["mirror"]],
		"topoShapeMap" : topoShapeMap,
		"topoMirrorIndices" : topoMirrorIndices,

		"allShape" : shapeOrdered,
		"mirrorShape" : [i for i in shapeOrdered
		                 if i in shapePoints["mirror"]],
		"shapeTopoMap" : shapeTopoMap,
		"shapeMirrorIndices" : shapeMirrorIndices,

		"data" : data,
	}

def populateMerge(mergeNode, nulls):
	""" look up 'point1' node in each null,
	retrieving actual point geometry """
	ordered = [i.node("point1") for i in nulls]
	network.populateMerge(
		targetMerge=mergeNode,
	    items=ordered,
		singleObjMerge=True
	)
	pass



def onNodeButtonPush():
	""" on direct node button press"""
	node = hou.pwd()

	topoSubnet = node.parm("toposubnet").eval()
	topoSubnet = hou.node(topoSubnet)
	topoMerge = hou.node(node.parm("topomerge").eval())

	shapeSubnet = node.parm("shapesubnet").eval()
	shapeSubnet = hou.node(shapeSubnet)
	shapeMerge = hou.node(node.parm("shapemerge").eval())

	if not (topoSubnet and shapeSubnet):
		print("No subnet nodes found, aborting")
		return
	if not (topoMerge and shapeMerge):
		print("No merge nodes found, aborting")
		return

	internalData = json.loads(node.parm("internaldata").eval() or "{}")

	topoMirrorParam = node.parm("topomirror")
	shapeMirrorParam = node.parm("shapemirror")

	result = pointProcessMain(
		topoSubnet,
		topoMerge,
		shapeSubnet,
		shapeMerge,
		data=internalData
	)
	topoMirrorParam.set(" ".join(
		[str(i) for i in result["topoMirrorIndices"]]))
	shapeMirrorParam.set(" ".join(
		[str(i) for i in result["shapeMirrorIndices"]]))

	result["data"]["prevTopoNodes"] = [i.path() for i in result["allTopo"]]

	node.parm("internaldata").set(json.dumps(result["data"]))


# groupNode = node.inputs()[1]
	#
	# groupParm = groupNode.parm("basegroup")
	# mirrorGroupString = ""
	#
	# shapeSubnet = node.parm("shapesubnet").eval()
	# shapeSubnet = hou.node(shapeSubnet)
	# shapeChildren = shapeSubnet.children()
	# shapeChildren = core.sortNodes(shapeChildren)
	# shapeMirrorBox = network.getNetworkBox(shapeSubnet, "mirror")
	#
	# topoNames = [i.name() for i in topoChildren]
	# shapeNames = [i.name() for i in shapeChildren]
	#
	# # update shape points if out of sync
	# for i, topoPoint in enumerate(topoChildren):
	# 	if topoPoint.type().name() == "geo":
	# 		# print topoPoint.name()
	# 		continue
	# 	if topoPoint.name() not in shapeNames:
	# 		topoPoint.copyTo(shapeSubnet)
	# 	if topoPoint in mirrorItems:
	# 		mirrorGroupString += "{} ".format(i)
	# 		shapePoint = shapeSubnet.node(topoPoint.name())
	# 		shapeMirrorBox.addItem(shapePoint)
	# 	# check mirror is correct
	#
	# #groupParm.set(mirrorGroupString)
	#
	# """ not robust to renaming topo points - if needed
	# give shape points a path link on creation"""
	# for shapePoint in shapeChildren:
	# 	if shapePoint.name() != topoNames:
	# 		shapePoint.destroy()

