# lib for adding and modifying attributes
import random
from edRig import core # can't import log :(
from maya import cmds
import maya.api.OpenMaya as om

dimTypes = {
	"0D" : ("matrix",),
	"1D" : ("nurbsCurve", "bezierCurve"),
	"2D" : ("nurbsSurface", "mesh")
}

def getMPlug(plugName):
	sel = om.MSelectionList()
	sel.add(plugName)
	return sel.getPlug(0)

def con(a, b, f=True):
	"""let's try this again"""
	cmds.connectAttr(a, b, f=f)

def conOrSet(a, b, f=True):
	"""connects plug to b if a is a plug,
	sets static value if not"""
	if isPlug(a):
		con(a, b, f)
	else:
		setAttr(b, attrValue=a)

# def getChildren(plug)

def breakConnections(target, source=True, dest=True):
	"""ed smash"""
	if core.isNode(target):
		for i in cmds.listAttr(target):
			breakConnections(target+"."+i, source, dest)
	if core.isPlug(target):
		for i in cmds.listConnections(target, plugs=True, s=source, d=dest):
			cmds.disconnectAttr(target, i)

def isNode(target):
	if "." in target:
		return False
	return cmds.objExists(target)

def isPlug(target):
	"""returns true for format pCube1.translateX"""
	node = target.split(".")[0]
	if not isNode(target):
		return False
	plug = ".".join(target.split(".")[1:])
	# print ""
	# print "plug is " + plug
	if plug in cmds.listAttr(node):
		return True
	return False

def processAttrNames(attr, node=None, asPlug=False, asAttr=True):
	"""absolute definite way of getting node.attr vs attr from any string"""
	returnList = []
	if asPlug:
		if node + "." in attr:
			returnList.append(attr)
		else:
			returnList.append(node+"."+attr)
	elif asAttr:
		if node+"." in attr:
			returnList.append("".join(attr.split(".")[:-1]))
	return returnList

# functions for using string attributes like keys in dictionary
def addTag(tagNode, tagName, tagContent=None, tagSuffix=False):
	tagName = tagName + "_tag" if tagSuffix else tagName
	if not tagName in cmds.listAttr(tagNode):
		cmds.addAttr(tagNode, ln=tagName, dt="string")
	if tagContent:
		# tag content can be anything, keep track of it yourself
		try:
			cmds.setAttr(tagNode + "." + tagName, tagContent, type="string")
		except:
			pass
	return tagNode+"."+tagName

def edTag(tagNode):
	# more tactile to have a little top tag
	happyList = [
		":)", ":D", ".o/", "^-^", "i wish you happiness",
		"bein alive is heckin swell!!!", "it's a beautiful day today",
		"we can do this", "you matter"
	]
	ey = random.randint(0, len(happyList) - 1)
	addTag(tagNode, tagName="edTag", tagContent=happyList[ey])
	cmds.setAttr(tagNode + ".edTag", l=True)

def checkTag(tagNode, tagName, tagContent):
	# checks if a node has a specific edTag
	testList = cmds.listAttr(tagNode, string="edTag")
	if testList:
		return True
	else:
		return False

def setTagsFromDict(tagNode, tagDict):
	for k, v in tagDict.iteritems():
		addTag(tagNode, k, v)

def getDictFromTags(tagNode):
	returnDict = {}
	for i in cmds.listAttr(tagNode):
		if "_tag" in i:
			tagName = i.split("_tag")[0]
			tagContent = cmds.getAttr(tagNode+"."+i)
			returnDict.update({tagName : tagContent})
	return returnDict

def listWithTagContent(searchNodes = [], searchTag="", searchContent=""):
	found = []
	for i in searchNodes:
		searchList = cmds.listAttr(i, string="*_tag")
		for n in searchList:
			if searchContent in cmds.getAttr(i+"."+n):
				found.append(i)
	return found


def getTag(tagNode, tagName=None):
	# retrieves specific tag information, or lists all of it
	if tagName:
		gotTag = cmds.getAttr(tagNode + "." + tagName)
	else:
		gotTag = cmds.listAttr(tagNode, string="*tag")
	return gotTag

def removeTag(tagNode, tagName=None):
	search = tagName if tagName else "*_tag"
	tags = cmds.listAttr(tagNode, string=search)
	for i in tags:
		cmds.deleteAttr(tagNode+"."+i)

BUILT_ATTR = "node_built"
def tagAsBuilt(node):
	"""used in conjunction with the listing principle
	to tell if a node needs to be reconstructed or not"""
	addAttr(node, attrName=BUILT_ATTR, dv=1, dt="bool")

def isBuilt(node):
	return BUILT_ATTR in cmds.listAttr(node)


def hideAttr(plug):
	cmds.setAttr(plug, cb=False)

def lockAttr(plug):
	cmds.setAttr(plug, locked=True)

def addAttr(target, attrName="newAttr", attrType="float", parent=None, **kwargs):
	"""wrapper for more annoying attr types like string
	returns plug"""
	if parent:
		if not target in parent:
			parent = target + "." + parent
		parent = ".".join(parent.split(".")[1:])
		kwargs.update({"parent" : parent})
		#print "parent is {}".format(parent)

	# check if already exists
	if attrName in cmds.listAttr(target):
		return target+"."+attrName

	dtList = ["string", "nurbsCurve"]
	if attrType in dtList:
		plug = cmds.addAttr(target, ln=attrName, dt=attrType, **kwargs)
	else:
		plug = cmds.addAttr(target, ln=attrName, at=attrType, **kwargs)
		# if you know the logic behind at vs dt, please contact me
	# contact me urgently
	if parent:
		return parent + "." + attrName
	return target+"."+attrName

def getAttr(*args, **kwargs):
	"""J U S T I N C A S E"""
	return cmds.getAttr(*args, **kwargs)


def makeAttrsFromDict(node, attrDict, parent=None):
	"""creates compound hierarchies from a dict
	:param attrDict : dict
	:param parent : string
	(compound plug)
	{"parent" : {
		"children" : { # sad times
			"mid" : {
				"children" : {
					"child" : { "dt" : "nurbsCurve"}
					}
				},
				"other" : { "dt" : "float",
							"min" : 0 }
					}"""
	"""the syntax including "children" key is clunky, but it's most explicit
	and futureproof for array attributes"""
	for k, v in attrDict.iteritems():
		if v.get("children"): # it's a compound
			parent = addAttr(node, attrName=k, attrType="compound",
			                 nc=len(v["children"].keys()))
			makeAttrsFromDict(node, v["children"], parent=parent)
		elif v.get("dt"): # it's a normal attribute
			kwargs = {nk : nv for nk, nv in v.iteritems() if nk != "dt"}
			addAttr(node, attrName=k, attrType=v["dt"], parent=parent, **kwargs)


INTERFACE_ATTRS = { # attribute templates for io network nodes
	"0D" : {"dt" : "matrix"},
	"1D" : {"children" : {
		"mainCurve" : {"dt" : "nurbsCurve"},
		"upCurve" : {"dt" : "nurbsCurve"}}},
	"2D" : {"dt" : "mesh"},
	"int" : {"dt" : "long"},
	#"message" : {"dt" : "message"}
	#ideally there would be a much closer link between this system and abstract attrs
	# give me a minute
	}

def setAttr(targetPlug, attrValue=None, absNode=None, **kwargs):
	"""similar wrapper for setAttr dealing with strings, matrices, etc
	absNode allows passing absoluteNode where performance is important"""
	if not attrValue:
		cmds.setAttr(targetPlug, **kwargs)

	elif isinstance(attrValue, basestring):
		# check for enum:
		#print "plug type is {}".format(plugType(targetPlug))
		if plugType(targetPlug) == "enum":
			setEnumFromString(targetPlug, attrValue)
		else:
			cmds.setAttr(targetPlug, attrValue, type="string")

	else:
		cmds.setAttr(targetPlug, attrValue, **kwargs)

def setAttrsFromDict(attrDict, node=None):
	"""expects dict of format {"attr" : value}"""
	for k, v in attrDict.iteritems():
		plug = node+"."+k if node else k
		setAttr(plug, v)

def setEnumFromString(plug, value):
	node, attr = tokenisePlug(plug)
	enumString = cmds.attributeQuery(attr, node=node, listEnum=True)[0]
	enumList = enumString.split(":")
	cmds.setAttr(plug, enumList.index(value))

def tokenisePlug(plug):
	"""atomic to get node and attr from plug"""
	print ""
	attr = ".".join(plug.split(".")[1:])
	node = plug.split(".")[0]
	print "node is {}, attr is {}".format(node, attr)
	return node, attr

def plugType(plug):
	"""returns string type for plugs"""
	# attr, node = tokenisePlug(plug)
	return cmds.getAttr(plug, type=True)

def getEnumValue(plug):
	"""current enum value as string"""
	return cmds.getAttr(plug, asString=True)

def getImmediateNeighbours(target, source=True, dest=True, wantPlug=False):
	"""returns nodes connected immediately downstream of plug, or all of node"""
	nodeList = []
	if core.isNode(target):
		for i in cmds.listAttr(target):
			nodeList += getImmediateNeighbours(i)
	else:
		plugs = cmds.listConnections(target, plugs=True, source=source, dest=dest)
		for i in plugs:
			nodeList.append((i.split(".")[0], i)) #node, plug
	return nodeList

def getDrivingPlug(plug):
	plugs = cmds.listConnections(plug, plugs=True, source=True, dest=False)
	if not plugs:
		return []
	return [i for i in plugs if i != plug][0]

def getImmediateFuture(target):
	return getImmediateNeighbours(target, source=False, dest=True)


def getImmediatePast(target):
	return getImmediateNeighbours(target, source=True, dest=False)

def makeMutualConnection(startNode, endNode, attrType="string",
                         startName="start", startContent=None,
                         endName="end"):
	"""base function for connecting two nodes"""
	startPlug = addAttr(startNode, attrName=startName, attrType=attrType)
	if startContent:
		setAttr(startPlug, startContent)
	endPlug = addAttr(endNode, attrName=endName, attrType=attrType)
	con(startPlug, endPlug)

def makeStringConnection(startNode, endNode,
						 startName="start", endName="end"):
	"""adds a string connection between two nodes"""
	makeMutualConnection(startNode, endNode, attrType="string",
	                     startName=startName, endName=endName)


def findPlugSource(startPlug):
	"""walk the graph backwards from an input plug
	until we find a plug without an input
	used to trace back control ui nodes"""
	stepBack = getDrivingPlug(startPlug)
	if not stepBack: # no driving plug found
		return stepBack
	return findPlugSource(stepBack)

def getTransformPlugs(node, t=True, r=True, s=True):
	"""returns list of plugs for specified node
	no more loops"""
	plugs = []
	mapping = {"translate" : t, "rotate" : r, "scale" : s}
	for i in [k for k, v in mapping.iteritems() if v]:
		for n in "XYZ":
			plugs.append(node + "." + i + n)
	return plugs

def unrollPlug(plug, returnLen=3):
	"""unrolls compound plug, and either curtails or fills in None up to length"""

def getNextAvailableIndex(arrayPlug):
	"""gets the first free index for an array attribute"""
	length = cmds.getAttr(arrayPlug, size=True)
	return arrayPlug+"[{}]".format(length)



# class ArgParse(object):
# 	"""experimental context handler to control creation and deletion
# 	of proxy nodes for functions."""



