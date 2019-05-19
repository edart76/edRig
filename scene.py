# operations for listing, grouping, adding to sets etc
from maya import cmds
#from edRig.core import ECA, AbsoluteNode
#import maya.api.OpenMaya as om

class Globals(object):
	"""holder for various singleton nodes and values"""
	nodes = {
		"ctrlBlue" : {
			"type" : "colorConstant",
			"attrs" : {
				"inColor" : (0,0,1) # pure blue
			}
		},
		"ctrlYellow": {
			"type": "colorConstant",
			"attrs" : {
				"inColor" : (1,1,0)
			}
		},
		"ctrlCyan": {
			"type": "colorConstant",
			"attrs": {
				"inColor": (0, 1, 1)
			}
		},
	}

	def invokeNode(self, nodeDict, name=None):
		"""creates a node from globals library or lists and returns it"""
		name = name or nodeDict["name"]
		test = cmds.ls(name)
		if test:
			return test[0]
		node = cmds.createNode(nodeDict["type"], name=name)
		if "attrs" in nodeDict:
			for k, v in nodeDict["attrs"].iteritems():
				cmds.setAttr(k, v)
		return node

	def __getattr__(self, item):
		if item in self.nodes:
			return self.invokeNode(self.nodes[item], name=item)
		return super(Globals, self).__getattr__(item)

def ls(*args, **kwargs):
	"""you know how maya returns None when it can't find anything
	don't you just love that"""
	result = cmds.ls(*args, **kwargs)
	return result or []

def listRelatives(*args, **kwargs):
	"""same as above"""
	result = cmds.listRelatives(*args, **kwargs)
	return result or []

# def parent(*args, **kwargs):
# 	"""for im"""

def listTaggedNodes(searchNodes=None, searchTag="", searchContent=None, searchDict={}):
	"""looks up all nodes with tag value that equals searchContent
	would be cool to enable this to search using a tag : content dict"""
	#print ""
	tests = searchNodes or listAllNodes()
	#print "tests are {}".format(tests)
	if searchDict:
		for k, v in searchDict.iteritems():
			tests = listTaggedNodes(tests, k, v)
		return tests

	returns = []

	for i in tests:
		if searchTag in cmds.listAttr(i):
			if searchContent:
				if cmds.getAttr(i+"."+searchTag) == searchContent:
					returns.append(i)
			else:
				returns.append(i)
	return returns

def listTopNodes():
	return listTopDags()
def listTopDags():
	return cmds.ls("|*", recursive=True)
def listAllNodes():
	"""all alphabetically"""
	return cmds.ls("*", recursive=True)

