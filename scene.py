# operations for listing, grouping, adding to sets etc
from maya import cmds
from edRig.node import ECA, AbsoluteNode, invokeNode
from edRig import attr
import maya.api.OpenMaya as om

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

	rootAttrs = {
		"assetNodesSelectable" : {
			"dt" : "bool",
			"dv" : False },
		"blackBoxAsset" : {
			"at" : "message"},
		"solvers" : {
			"at" : "message",
			"multi" : True,
		},
		"materials": {
			"at" : "string",
			"multi" : True,
		}
		}


	def __init__(self):
		pass

	@property
	def globalsRoot(self):
		node = invokeNode("globals_root", "network")
		if not attr.isBuilt(node):
			self.buildGlobalsRoot(node)
		return node

	def buildGlobalsRoot(self, node):
		"""usually indicates everything else needs building too"""
		attr.makeAttrsFromDict(node, self.rootAttrs)
		attr.tagAsBuilt(node)

	@property
	def blackBoxAsset(self):
		"""returns special asset node used to make shapes unselectable
		kill me"""
		asset = ls("globals_blackBoxAsset")
		if asset:
			return asset
		else:
			asset = cmds.container("globals_blackBoxAsset")
			cmds.setAttr(asset+".blackBox", 1)
			attr.makeMutualConnection(self.globalsRoot, asset,
			                          attrType="message", startName="blackBoxAsset",
			                          endName="globalsRoot")
			return asset

	def addSolver(self, solver):
		"""catalogues solver properly"""
		attr.makeMutualConnection(self.globalsRoot, solver, attrType="message",
		                          startName="solvers", endName="globalsRoot")

	@property
	def globalsControl(self):
		node = AbsoluteNode(invokeNode("globals_ctrl", "transform"))
		for i in node.TRS():
			attr.setAttr(i, l=True, cb=False)
		return node

def addToAsset(assetName=None, targetNode=None):
	"""very skittish of all this stuff"""
	cmds.container(assetName, force=True, addNode=targetNode)

def removeFromAsset(assetName=None, targetNode=None):
	"""very skittish of all this stuff"""
	cmds.container(assetName, force=True, removeNode=targetNode)












SceneGlobals = Globals()

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

def newScene():
	"""forces new maya scene"""
	cmds.file(new=True, f=True)


def alembicExport(targetSets=None, startFrame=None, endFrame=None):
	"""exports AND TAGS geometry from the target sets,
	or from every set contained in alembic_geo
	start and end frame default to scene timeline"""


