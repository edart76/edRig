# lib for adding and modifying attributes
# framestore pls no sue
from edRig import core
from maya import cmds
import maya.api.OpenMaya as om

def breakConnections(target, source=True, dest=True):
	"""ed smash"""
	if core.isNode(target):
		for i in cmds.listAttr(target):
			breakConnections(target+"."+i, source, dest)
	if core.isPlug(target):
		for i in cmds.listConnections(target, plugs=True, s=source, d=dest):
			cmds.disconnectAttr(target, i)

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
def addTag(tagNode, tagName, tagContent=None, tag=True):
	if not tagName + "_" in cmds.listAttr(tagNode):
		if tag:
			cmds.addAttr(tagNode, ln=tagName+"_tag", dt="string")
		else:
			cmds.addAttr(tagNode, ln=tagName, dt="string")
	if tagContent:
		# tag content can be anything, keep track of it yourself
		cmds.setAttr(tagNode + "." + tagName + "_tag", tagContent, type="string")

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

def listTaggedNodes(searchTag="", searchType=None):
	if searchType:
		allDag = cmds.ls(type=searchType)
	else:
		allDag = cmds.ls(dagObjects=True)
	tag = searchTag+"_tag" if searchTag else "_tag"
	returnList = []
	for i in allDag:
		for n in cmds.listAttr(i):
			if tag in n:
				returnList.append(i)
	return returnList

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

def hideAttr(plug):
	cmds.setAttr(plug, cb=False)

def lockAttr(plug):
	cmds.setAttr(plug, locked=True)

def addAttr(target, attrName="newAttr", attrType="float", **kwargs):
	"""wrapper for more annoying attr types like string
	returns plug"""
	if attrType == "string":
		plug = cmds.addAttr(target, ln=attrName, dt="string", **kwargs)
	else:
		plug = cmds.addAttr(target, ln=attrName, at=attrType, **kwargs)
	return plug

def getImmediateNeighbours(target, source=True, dest=True):
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
	return [i for i in plugs if i != plug][0]

def getImmediateFuture(target):
	return getImmediateNeighbours(target, source=False, dest=True)


def getImmediatePast(target):
	return getImmediateNeighbours(target, source=True, dest=False)





