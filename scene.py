# operations for listing, grouping, adding to sets etc
from edRig.node import ECA, AbsoluteNode, invokeNode
from edRig import cmds, om, attr, core
import traceback


class SceneObject(object):
	""" base class for conceptual objects in maya scene,
	keeping related elements grouped """

	@classmethod
	def invokeNode(cls, name, type="transform", parent="", func=None):
		func = func or ECA
		return invokeNode(name, type, parent, func)



class TidyManager(object):
	"""manage execution of ops"""
	excludeList = [
		"tilePile",
	]
	def __init__(self, tidyGrp, excludeList=None):
		""":param string : tidyGrp"""

		self.tidyGrp = tidyGrp
		self.beforeSet = None
		self.afterSet = None
		if excludeList: self.excludeList = excludeList

	def __enter__(self):
		self.beforeSet = set(listAllNodes())
		self.dag = invokeNode(self.tidyGrp, type="transform")
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""clean up TOP LEVEL maya scene nodes regardless"""
		self.afterSet = set(listAllNodes())
		new = self.afterSet - self.beforeSet
		newDags = [n for n in [AbsoluteNode(i) for i in new] if n.isDag()
		           and not n.parent]
		newDags = [i for i in newDags if i not in self.excludeList
		           and not cmds.listRelatives(i, parent=True)]

		for i in new:
			pass
		for i in newDags:
			current = listRelatives(self.dag, ad=True)
			#print "current {}".format(current)
			if not i in current:
				try:
					cmds.parent(i, self.dag)
				except:
					pass
		# halt execution
		if exc_type:
			self.printTraceback(exc_type, exc_val, exc_tb)
			pass

	@staticmethod
	def printTraceback(tb_type, tb_val, tb):
		traceback.print_exception(tb_type, tb_val, tb)

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


# --- NAMESPACES
def addNamespace(name):
	""" wrapper to squash errors on existing and nested namespaces """
	print("name {}".format(name))
	print("split {}".format(name.split(":")))
	for i, val in enumerate(name.split(":")):

		space = ":".join(name.split(":")[:i+1])
		print("namespace {}".format(space))
		if not cmds.namespace(exists=space):
			cmds.namespace(addNamespace=space)
			# add network node to let namespace survive save and load
			network = cmds.createNode("network", n=space+":marker")

def removeNamespace(name, deleteNodes=False):
	if name[0] != ":" : name = ":" + name
	print("name {}".format(name.split(":")))
	for i, val in enumerate(name.split(":")):
		#space = ":".join(name.split(":"))
		space = name.split(":")[-1]
		parent = ":".join(name.split(":")[:-(i+2)]) or ":"
		print("namespace {}, parent {}".format(space, parent))
		if cmds.namespace(exists=space):
			if deleteNodes:
				cmds.delete( cmds.namespaceInfo(space,
				                listOnlyDependencyNodes=1, internal=1))
				cmds.namespace(removeNamespace=space)
			else:
				cmds.namespace(removeNamespace=space,
				               mergeNamespaceWithParent=1)

def pruneRemnantSpaces():
	""" most namespaces get left with only some random render layer
	or material nodes keeping them alive
	this assumes that if namespace contains no dag nodes,
	we probably won't miss it """
	cmds.namespace(setNamespace=":") # root
	spaces = cmds.namespaceInfo(listOnlyNamespaces=1, recurse=1)
	if not spaces: return
	for i in spaces:
		hasDag = False
		for n in cmds.namespaceInfo(i, listOnlyDependencyNodes=1):
			if "kDagNode" in cmds.nodeType(i, inherited=1, api=1):
				hasDag = True
		if not hasDag:
			removeNamespace(i, deleteNodes=1)





