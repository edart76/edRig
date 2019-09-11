## encapsulating saving and loading dimensional objects
# saving, loading and reapplying in general
# goal is to have a "magic button" akin to Framestore's
# data storage
#from collections import MutableMapping
import edRig.node
from edRig.structures import SafeDict, AttrItem

from edRig import core, attrio, mesh, curve, surface, attr
from edRig.node import AbsoluteNode, ECA
#from edRig.tesserae.ops.op import Op
from edRig.layers import Env
import copy
from maya import cmds
# import maya.api.OpenMaya as om
# import maya.api.OpenMayaAnim as oma
import pprint

class Memory(object):
	"""stores maya scene data in regular, serialisable container
	it would be cool to have this link live to the op datafile to
	allow different workflows when editing, but one step at a time"""
	infoKinds = ["attr", "xform", "weight", "shape", "multi"]

	def __init__(self, *args, **kwargs):
		super(Memory, self).__init__(*args, **kwargs)
		self.nodes = []
		self._storage = dict(*args, **kwargs)

	def __getitem__(self, key):
		if not key in self._storage.keys():
			return False
		else:
			return self._storage[key]


	def __setitem__(self, key, value):
		self._storage[key] = value

	def __delitem__(self, key):
		del self._storage[key]

	def __iter__(self):
		return iter(self._storage)

	def __len__(self):
		return len(self._storage)

	def __repr__(self):
		return self._storage.__repr__()


	# achieve live linking by refreshing memory once before op plan and run

	def _allocateSpace(self, infoName, nodes=None):
		"""creates blank memory dict
		one memory cell per node"""
		self._storage[infoName] = {}
		self._storage[infoName]["closed"] = False
		self._storage[infoName]["nodes"] = nodes
		self.nodes += nodes

		"""currently fragile, expecting to be called just once per data
		does not yet support addition"""

		"""use:
		{"joints" : {
			"nodes" : ["joint1", "joint2" etc],
			"xform" : [
				{
					"translate" : (010), 
					"rotate" : (204),
					etc
					}
				],
			"attr" : [etc, etc]
			},
		"curve" : {etc}
		}
		no memory cell will ever store different infotypes per node"""

	def infoNames(self):
		return self._storage.keys()

	def infoTypes(self, infoName):
		return self._storage[infoName].keys()

	def remember(self, infoName, infoType, nodes=None, **kwargs):
		"""add information to op's memory if none exists
		we remember lists here
		main entrypoint"""

		# multi memory support
		if isinstance(infoType, list):
			for i in infoType:
				self.remember(infoName, i, nodes)

		if not isinstance(nodes, list):
			nodes = [nodes]
		if not infoName in self.infoNames():
			#print "allocating blank space for {}".format(infoName)
			self._allocateSpace(infoName, nodes=nodes)

		if not infoType in self._storage[infoName].keys():
			#print "gathering goss, making blank info"
			# only gather info if none exists??
			self._storage[infoName][infoType] = self.makeBlankInfoType(infoType)

			# pre-existing information will not be lost, nodes will still be refreshed

			gatheredGoss = [self._gatherInfo(infoType, target=i, **kwargs) for i in nodes]
			self._storage[infoName][infoType] = gatheredGoss
		# always set node regardless to ensure info is relevant in scene
		# self.setNode(infoName, core.AbsoluteNode(node))
		self._storage[infoName]["nodes"] = [edRig.node.AbsoluteNode(i) for i in nodes]
		#print ""



	def recall(self, infoName, infoType="all", **kwargs):
		"""retrieve saved info AND APPLY IT """
		if not infoType in self.infoKinds and infoType != "all":
			raise RuntimeError("infoType {} is not recognised".format(infoType))
		if infoType == "all":
			# returnDict = {}
			# returnDict.clear()
			for i in self.infoKinds.remove("all"):
				# returnDict[i] = self.recall(infoName, infoType=i)
				self.recall(infoName, infoType=i)
			#return returnDict
		else:
			# return self._storage[infoName][infoType]
			self._applyInfo(infoName, infoType,
			                target=self.nodesFromInfoName(infoName),
			                **kwargs)

	def refresh(self, infoName="", infoType="", *args, **kwargs):
		"""updates existing memory with info from scene
		DOES NOT create new info if none exists"""
		print
		print "memory refresh - nodesFromInfoName {} are {}".format(
			infoName, self.nodesFromInfoName(infoName))
		gatheredGoss = [self._gatherInfo(infoType, target=i)
		                for i in self.nodesFromInfoName(infoName)]
		self._storage[infoName][infoType] = gatheredGoss
		print "{}-{} is now {}".format(infoName, infoType,
		                               self._storage[infoName][infoType])

	def remove(self, infoName, infoType=None):
		"""clears memory selectively without going into the datafile
		take note FS"""
		if infoType:
			self._storage[infoName].pop(infoType, None)
		else:
			self._storage.pop(infoName, None)

	def renewableMemory(self):
		"""returns all memory slots that have a value - eg that
		can be renewed from scene"""
		# returnDict = copy.deepcopy(self._storage) # NOT FOR DIRECT UPDATE
		# USE ONLY AS GUIDE - USE REFRESH TO UPDATE MEMORY
		returnDict = {}
		#pprint.pprint("storage is {}".format(self._storage))
		for k, v in self._storage.iteritems():
			if k == "nodes" :
				continue
			#print "k is {}, v is {}".format(k, v)
			if v.get("closed"):
				continue
			returnDict[k] = []
			for vk in v.keys():
				#print "vk is {}".format(vk)
				if vk == "nodes" or vk == "closed" :
					continue
				returnDict[k].append(vk)
		return returnDict

	def _gatherInfo(self, infoType, target=None, **kwargs):
		"""implements specific methods of gathering information from scene
		could have done some fancy metamethod but i am but a basic boi"""
		target = AbsoluteNode(target)
		if infoType not in self.infoKinds:
			raise RuntimeError("cannot gather info of type {}".format(infoType))
		if not cmds.objExists(target):
			raise RuntimeError("no object found named {}".format(target))

		print ""
		print "GATHERING GOSS"

		returnDict = {}
		target = edRig.node.AbsoluteNode(target)  # speed
		attrList = []
		if infoType == "attr":
			# gather dict of attribute names and values
			# all of them?
			if "allAttrs" in kwargs and kwargs["allAttrs"]:
				attrList = cmds.listAttr(target, settable=True)  # very risky
			# attr can register transform attrs, but only if directed
			elif not kwargs.get("transformAttrs"):
				omitList = ["translate", "rotate", "scale"]
				baseList = cmds.listAttr(target, cb=True)
				#attrList = [i for i in baseList if not (any(omitList) in i)]
				for i in baseList:
					if not i.split(".")[-1] in omitList:
						attrList.append(i)
					else:
						continue
			else:
				attrList = cmds.listAttr(target, cb=True)  # channelbox
			for i in attrList:
				returnDict[i] = attr.getAttr(target + "." + i)
			# we will absolutely need more nuanced handling down the line,
			# but this is fine for now

		elif infoType == "xform":
			# speed is not yet of the essence
			for space, truth in zip(["world", "local"], (True, False)):
				returnDict[space]["translate"] = cmds.xform(target, q=True, ws=truth, t=True)
				returnDict[space]["rotate"] = cmds.xform(target, q=True, ws=truth, ro=True)
				returnDict[space]["scale"] = cmds.xform(target, q=True, ws=truth, s=True)
			if "jointMode" in kwargs and "jointMode":
				for ax in "XYZ":
					jointOrient = cmds.getAttr(target + ".jointOrient" + ax)
					returnDict["jointOrient" + ax] = jointOrient
				returnDict["rotateOrder"] = cmds.getAttr(target + ".rotateOrder")


		elif infoType == "weight":
			# woah there
			#raise NotImplementedError("not yet fool")
			returnDict = self.getWeightInfo(targetNode=target, targetAttr=None)

		elif infoType == "shape":
			# this is where the fun begins
			if not target.shapeFnType:
				raise RuntimeError("tried to gather the shape of shapeless")
				pass
			returnDict = self.getShapeInfo(target)
		#print "gathered goss is {}".format(returnDict)
		return returnDict

	def _applyInfo(self, infoName, infoType, target=None,
	               relative=None, **kwargs):
		allInfo = self.infoFromInfoName(infoName)

		space = kwargs.get("space") or "world"

		if not isinstance(target, list):
			index = self.indexFromNode(infoName, target)
			info = [allInfo[infoType][index]]
			target = [target]
		else:
			info = allInfo[infoType]

		#print "info to apply is {}".format(info)
		# it's really, really for the best if you just work by sequence
		for target, info in zip(target, info):
			if not cmds.objExists(target):
				raise RuntimeError("APPLYINFO TARGET {} DOES NOT EXIST".format(target))
			if infoType == "attr":
				for k, v in info.iteritems():
					#print "setting attr {}.{} to {}".format(target, k, v)
					attr.setAttr(target + "." + k, v)

			elif infoType == "xform":
				cmds.xform(target, ws=True, t=(info[space]["translate"]))
				cmds.xform(target, ws=True, ro=info[space]["rotate"])
				cmds.xform(target, ws=True, s=info[space]["scale"])

			elif infoType == "weight":
				# nope
				pass

			elif infoType == "shape":
				self.setShapeInfo(info, target=target)
				pass

	def indexFromNode(self, infoName, node):
		return self._storage[infoName]["nodes"].index(node)

	def nodesFromInfoName(self, infoName):
		"""returns list of all nodes tracked by infoName"""
		return [AbsoluteNode(i) for i in self._storage[infoName]["nodes"]]

	def infoFromInfoName(self, infoName):
		return self._storage[infoName]

	def setNodes(self, infoName, nodes):
		if not isinstance(nodes, list):
			nodes = [nodes]
		self._storage[infoName]["nodes"] = nodes

	def getFlattenedNodes(self):
		"""ensure nodes are stored as strings, not AbsNodes"""
		#self.nodes = [str(i) for i in self.nodes] # for some reason | characters screw up strings
		return [str(i) for i in self.nodes]

	def flattenNodes(self):
		for k, v in self._storage.iteritems():
			v["nodes"] = [str(i) for i in v["nodes"]]

	def restoreAbsoluteNodes(self):
		"""restore strings to absNodes, assuming the same names exist"""
		self.nodes = [edRig.node.AbsoluteNode(i) for i in self.nodes]
		for k, v in self._storage.iteritems():
			print "k is {}, v is {}, v keys are {}".format(k, v, v.keys())
			if "nodes" in v.keys():
				v["nodes"] = [edRig.node.AbsoluteNode(i) for i in v["nodes"]]
			print "restored {}".format(v["nodes"])
		pass

	@staticmethod
	def makeBlankInfoType(infoType):
		"""in case special types need special templates"""
		typeDict = {
			"attr": [],
			"xform": {"local" : [],
			          "world" : []},  # worldspace transforms
			"weight": [],
			"shape": [],
		}
		return {infoType : typeDict[infoType],
				"closed" : False}

	def setClosed(self, infoName, infoType=None, status=True):
		"""prevent a memory infotype or whole cell from being refreshed"""
		if infoType:
			self._storage[infoName][infoType]["closed"] = status
		else:
			self._storage[infoName]["closed"] = status

	# info type-specific methods
	@staticmethod
	def getShapeInfo(target):
		if not target.isShape():
			raise RuntimeError
		info = {}
		if target.isCurve:
			info = curve.getCurveInfo(target)
			info["shapeType"] = "nurbsCurve"
		elif target.isMesh:
			info = mesh.getMeshInfo(target)
			info["shapeType"] = "mesh"
		elif target.isSurface:
			info = surface.getSurfaceInfo(target)
			info["shapeType"] = "nurbsSurface"
		pass
		return info

	@staticmethod
	def setShapeInfo(info, target):
		"""recreates a shape node directly from the api
		:param info: dict
		:param target = AbsoluteNode"""
		parent = target.transform # shape nodes are irrelevant
		kSuccess = False
		if target.isCurve and info.get("shapeType") == "nurbsCurve":
			kSuccess = curve.setCurveInfo(info, target, parent=parent)

		elif target.isSurface and info.get("shapeType") == "nurbsSurface":
			kSuccess = surface.setSurfaceInfo(info, target, parent=parent)

		else:
			print "shape regen failed for some reason, likely mismatch in shapeType - try refreshing"
			return


		# if kSuccess:
		#


		pass

	@staticmethod
	def getWeightInfo(targetNode=None, targetAttr=None,
	                  targetShape=None):
		"""save out weights of target attr of target node (deformer) on target shape
		return massive tuples"""
		# if targetAttr is not specified, save for ALL paintable attributes
		paintable = mesh.getPaintable(targetShape)

	def setWeightInfo(self, targetNode=None, targetAttr=None, targetShape=None,
	                  weights=None):
		"""reapply weights on to target shape"""

	def serialiseMemory(self):
		"""is it this simple?"""
		# self._storage["nodes"] = self.getFlattenedNodes()
		self.flattenNodes()
		return self._storage

	def reconstructMemory(self, memoryDict):
		self._storage = copy.deepcopy(memoryDict) or {}
		#self.restoreAbsoluteNodes()
		return self

class OpAttrItem(AttrItem):
	""" i have had it with these mumblin fumblin trees
	 in my monday to friday dict
	 op io is currently a warzone - this should help with that
	 compound and array attrs are paramount
	 actually just basic functionality is paramount"""

	def __init__(self, role="input", dataType="0D",
	             hType="leaf", name="blankName", default=None, desc="",
	             *args, **kwargs):
		super(OpAttrItem, self).__init__(role=role, dataType=dataType,
		                                 hType=hType, name=name)
		self.role = role
		self.children = []
		self._name = name
		self._dataType = dataType
		self._hType = hType  # hierarchy type - leaf, compound, array, root, dummy
		self._value = None
		self.controller = None
		self.connections = [] # list of string names and addresses
		self.default = default
		self.desc = desc
		self.extras = SafeDict(kwargs) # can't account for everything
		self.parent = None # risky but handy

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, val):
		self._name = val

	@property
	def value(self):
		if not self._value and self.default:
			return self.default
		return self._value

	@value.setter
	def value(self, val):
		self._value = val

	@property
	def dataType(self):
		return self._dataType

	@dataType.setter
	def dataType(self, val):
		self._dataType = val

	@property
	def hType(self):
		return self._hType

	@hType.setter
	def hType(self, val):
		self._hType = val

	def isLeaf(self):
		return self.hType == "leaf"

	def isCompound(self):
		return self.hType == "compound"

	def isArray(self):
		return self.hType == "array"

	def isConnectable(self):
		# print "testing if {} is connectable".format(self.name)
		# print "attr hType is {}".format(self.hType)
		# print "result is {}".format(self.hType == "leaf" or self.hType == "compound")
		return self.hType == "leaf" or self.hType == "compound"

	def isInteractible(self):
		"""not all ui widgets should be connectable"""
		return self.isConnectable() or self.isDummy()

	def isDummy(self):
		"""used if you want input functionality but not an actual connection"""
		return  self.hType == "dummy"

	def isMulti(self):
		"""alright this is kind of getting away from me but this is used
		to allow multiple connections to a single input
		it's literally just for skinOp"""
		return self.extras["multi"]

	def addChild(self, newChild):
		if self.hType == "leaf":
			raise RuntimeError("CANNOT ADD CHILD ATTRIBUTES TO LEAF")
		self.children.append(newChild)
		newChild.parent = self

	def getChildren(self):
		if self.isLeaf():
			return []
		return sorted(self.children)

	def getAllChildren(self):
		allChildren = []
		level = self.getChildren()
		for i in level:
			if not i.isLeaf():
				allChildren += i.getAllChildren()

			allChildren.append(i)
		print "getAllChildren is {}".format(allChildren)
		return sorted(allChildren)

	def getAllLeaves(self):
		level = self.getAllChildren()
		return [i for i in level if i.isLeaf()]

	def getAllConnectable(self):
		level = self.getAllChildren()
		levelList = [i for i in level if i.isConnectable()]
		if self.isConnectable():
			levelList.append(self)
		return levelList

	def getAllInteractible(self):
		level = self.getAllChildren()
		levelList = [i for i in level if i.isInteractible()]
		if self.isInteractible():
			levelList.append(self)
		return levelList

	def getConnections(self):
		return self.connections

	def setConnections(self, val):
		"""add maya plug support"""
		super(OpAttrItem, self).setConnections(val)
		for i in val:
			if self.role == "input":
				cmds.connectAttr(i.plug, self.plug)
			else:
				cmds.connectAttr(self.plug, i.plug)

	@staticmethod
	def opHierarchyFromDict(fromDict, role="input", value=None, name="newAttr"):
		newAttr = OpAttrItem(name=name, dataType=fromDict["dataType"],
		                     hType=fromDict["hType"], value=value, role=role,
		                     desc=fromDict["desc"])
		if "children" in fromDict.keys():
			for i in fromDict["children"]:
				newAttr.addChild(OpAttrItem.opHierarchyFromDict(i,
					role=role, value=i["value"], name=i["name"]))
		return newAttr

	def serialise(self):

		for i in self.getConnections():
			i["attr"] = i["attr"].name
		returnDict = {"hType" : self.hType,
		              "dataType" : self.dataType,
		              "role" : self.role,
		              "value" : self.value if isinstance(self.value, (int, str, float)) else None,
		              "connections" : self.getConnections(),
		              "children" : [i.serialise() for i in self.getChildren()],
		              "name" : self.name,
		              "desc" : self.desc,
		              "extras" : self.extras
		              }
		return returnDict

	@staticmethod
	def fromDict(fromDict, role="input"):
		if not fromDict:
			return
		newItem = OpAttrItem(role=role)
		newItem.name = fromDict["name"]
		newItem.dataType = fromDict["dataType"]
		newItem.hType = fromDict["hType"]
		newItem.value = fromDict["role"]
		newItem.connections = fromDict["connections"]
		newItem.children = [newItem.fromDict(i, role=role) for i in fromDict["children"]]
		newItem.extras = fromDict["extras"]
		newItem.desc = fromDict["desc"]
		return newItem

	def attrFromName(self, name):
		print "attrFromName looking for {}".format(name)
		if self.name == name:
			return self
		elif self.getChildren():
			results = [i.attrFromName(name) for i in self.getChildren()]
			return next((i for i in results if i), None)
		else:
			return None

	### user facing methods
	def addAttr(self, name="", hType="leaf", dataType="0D",
	            default=None, desc="", *args, **kwargs):
		print "attrItem addAttr name is {}".format(name)
		if self.isLeaf():
			raise RuntimeError("CANNOT ADD ATTR TO LEAF")
		# check if attr of same name already exists
		if self.attrFromName(name):
			raise RuntimeError("ATTR OF NAME {} ALREADY EXISTS".format(name))
		newAttr = OpAttrItem(name=name, hType=hType, dataType=dataType,
		                     default=default, role=self.role, desc=desc,
		                     *args, **kwargs)
		self.addChild(newAttr)
		return newAttr

	def removeAttr(self, name):
		# first remove target from any attributes connected to it
		target = self.attrFromName(name)
		if not target:
			Env.log("attr {} not found and cannot be removed, skipping".format(name))
			return
		# what if target has children?
		for i in target.getChildren():
			target.removeAttr(i.name)
		for i in target.getConnections():
			conAttr = i["attr"]
			conAttr.connections = [i for i in conAttr.connections if i["attr"] != self]
		# remove attribute
		self.children = [i for i in self.getChildren() if i.name != name]
		# THE DOWNSIDE: when messing with live attributes, everything updates live
		# cannot say when to refresh connections. user must be careful when deleting

	def copyAttr(self):
		"""used by array attrs - make sure connections are clean
		AND NAMES ARE UNIQUE"""
		newAttr = copy.deepcopy(self)
		for i in newAttr.getAllChildren():
			i.connections = []
		return newAttr

	def getExtra(self, lookup):
		"""get enum options and other stuff"""
		return self.extras[lookup]

	@property
	def opGrp(self):
		return core.invokeNode(name=self.opName+"_opGrp", type="transform",
		                       parent=self.controller.rigGrp)

class InvokedNode(object):
	def __init__(self, name, nodeType="transform",
	             parent=None, parentOp=None):
		self.name = name
		self.nodeType = nodeType
		self.parentOp = parentOp
		self.parent = parent

	def __repr__(self):
		if cmds.objExists(self.name):
			return AbsoluteNode(self.name)
		else:
			return self.makeNode()

	def makeNode(self):
		if self.parentOp:
			node = self.parentOp.ECA(self.nodeType, name=self.name)
		else:
			node = ECA(self.nodeType, name=self.name)
		if self.parent:
			cmds.parent(node, self.parent)
		return node


class InvokedNodeDescriptor(object):
	"""same as above but it actually works"""
	def __init__(self, name, nodeType="transform", parent=None):
		"""name and parent should include namespaces"""
		self.name = name
		self.parent = parent
		self.nodeType = nodeType

	def __get__(self, instance, owner):
		test = cmds.ls(self.name)
		if not test:
			node = ECA(self.nodeType, n=self.name)
		else:
			node = test[0]
		if cmds.objExists(self.parent) and node.isDag():
			cmds.parent(node, self.parent)
		return node


	

class SetupBase(object):
	# main mechanism to save out and load information
	def __init__(self, path=None, name=None):
		self.path = path
		self.name = name

	def matchSaved(self):
		pass

	def getDataDict(self):
		return attrio.getData()

	pass


class Setup1D(SetupBase):
	# setup jointCurves
	def __init__(self, path=None, name="1D"):
		super(Setup1D, self).__init__(path=path, name=name)

