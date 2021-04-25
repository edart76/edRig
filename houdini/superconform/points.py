
from edRig import hou
from edRig.houdini import core, network
reload(core)
reload(network)

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
	topoChildren = list(filter(
		lambda x: (x.type() in conformNodeTypes), topoChildren))

	# check for mirror membership
	mirrorBox = network.getNetworkBox(topoSubnet, "mirror")
	mirrorItems = set(network.itemsInNetworkBox(mirrorBox))
	# only nulls
	mirrorItems.intersection_update(set(topoChildren))
	single = set(topoChildren) - set(mirrorItems)

	# mirrored topo point creates two shape points,
	# but one created point will be mirrored by default

	return {"single" : single, "mirror" : mirrorItems}

def validateTopoPointNaming(singleNodes):
	"""check naming of topo point nodes - singles are given "C_" if
	not otherwise defined"""
	sides = "LRC"
	for node in singleNodes:
		if not (node.name()[1] == "_" and node.name()[0].upper() in sides):
			node.setName("C_" + node.name())
		elif not node.name()[0].isupper(): # enforce upper case
			node.setName(node.name()[0].upper() + node.name()[1:])


# path connections are used to make system robust to renaming

folderLabel = "Connected Points"
parmLabel = "Point"
def addPointPathConnections(point):
	""" ensure that each topo point has one or two path parametres
	pointing to its corresponding shape points """


	group = point.parmTemplateGroup()
	folderTemplate = hou.FolderParmTemplate(
		"pointfolder", folderLabel,
		folder_type=hou.folderType.ScrollingMultiparmBlock,
		default_value=0,
	    ends_tab_group=False)
	pathTemplate = hou.StringParmTemplate("pointop#", parmLabel, 1,
	    string_type=hou.stringParmType.NodeReference)
	pathTemplate.setTags({"opfilter": "!!OBJ/NULL!!", "oprelative": ".", "script_callback_language": "python"})
	folderTemplate.addParmTemplate(pathTemplate)
	group.append(folderTemplate)
	point.setParmTemplateGroup(group)
	point.setParmTemplateGroup(group)

def checkPointParms(point):
	""" check that conform point has expected connections """
	group = point.parmTemplateGroup()
	if not group.findFolder(folderLabel):
		addPointPathConnections(point)
	# check path value
	path0 = group.find(parmLabel+"0")
	print(path0)



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

def pointProcessMain(topoSubnet, shapeSubnet):
	""" main function run by superconform point processing """
	topoPoints = gatherTopoPoints(topoSubnet)
	validateTopoPointNaming(topoPoints["single"])


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

