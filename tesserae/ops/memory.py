"""
ANOTHER refit of memory - memory system is now only a wrapper AROUND
basic tree data
"""
from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
from functools import partial
from enum import Enum
import pprint
import copy
from edRig import cmds, om, ECA, AbsoluteNode
from edRig import attr, transform, curve, mesh, surface
from edRig.lib.python import AbstractTree

# example dict structure
{"joints": {
	"nodes": ["joint1", "joint2", ...],
	"xform": [
		{
			"translate": (13),
			"rotate": (204),
			... : ...
		}
	],
	"attr": [..., ...]
},
	"curve": {...}
}

class InfoTypes(Enum):
	Attr = "attr",
	Xform = "xform",
	Weight = "weight",
	Shape = "shape"

# class Memory2(AbstractTree):
class Memory2(object):
	""" a long time ago Matt Goutte told me that trees are all you need
	in cg
	he was so right

	each branch of the data tree is a separate named memory cell,
	applying to a single set of nodes
	each cell may contain data of different types - eg attr, xform

	"""
	infoKinds = ["attr", "xform", "weight", "shape", "multi"]

	def __init__(self, dataTree:AbstractTree):
		self.data = dataTree

	def __getitem__(self, item):
		return self.data[item]
	def __setitem__(self, key, value):
		self.data[key] = value
	def __call__(self, *args, **kwargs):
		return self.data(*args, **kwargs)

	def get(self, key, default=None):
		return self.data.get(key, default)

	@property
	def nodes(self)->set:
		"""return all nodes that this memory accesses"""
		nodes = set()
		for cell in self.data.branches:
			nodes.update(set(cell["nodes"]))
		return nodes

	def infoNames(self):
		"""return names of all named branches"""
		return list(self.data.keys())

	def cellInfoTypes(self, cellName):
		"""all types of data in the given cell"""
		return list(self[cellName].keys())

	def _allocateNamedCell(self, infoName, nodes=None):
		"""creates blank named memory cell,
		as a new branch in data tree
		"""
		nodes = nodes or []
		if self.get(infoName):
			return

		# create branch
		self[infoName] = {
			"nodes" : nodes
		}

	def _allocateTypeCell(self, cellName, infoType, nodes=None):
		"""initialise a memory cell of given name and type"""
		if not cellName in self.infoNames():
			self._allocateNamedCell(cellName, nodes=nodes)

		if not infoType in list(self[cellName].keys()):
			self[cellName][infoType] = self.makeBlankInfoType(
				infoType)

	def remove(self, infoName, infoType=None):
		"""clears memory selectively without going into the datafile
		take note FS"""
		if infoType:
			self[infoName].pop(infoType, None)
		else:
			self.data.pop(infoName, None)

	def renewableMemory(self):
		"""returns all memory slots that have a value - eg that
		can be renewed from scene"""
		returnDict = {}
		for i in self.data.branches:

			if i.get("closed"):
				continue
			returnDict[i.name] = []

			for n in list(i.value.keys()):
				#print("n branch {}".format(n))
				if n == "nodes" or n== "closed":
					continue
				returnDict[i.name].append(n)
		return returnDict


	# region Maya systems
	def registerData(self, infoName, infoType, nodes:List=None, **kwargs):
		"""
		main entrypoint
		sets up memory if name/type does not exist,
		then registers info
		we remember lists here
		"""
		print(("remember infoName {}, infotype {}, nodes {}".format(
			infoName, infoType, nodes)
		))

		# multi memory support - register multiple data types
		if isinstance(infoType, list):
			for i in infoType:
				self.registerData(infoName, i, nodes)
			return


		self._allocateTypeCell(infoName, infoType, nodes=nodes)

		#if not self[infoName][infoType]:
		gatheredGoss = [self._gatherInfo(
			infoType, target=i, **kwargs) for i in nodes]
		self[infoName][infoType] = gatheredGoss

		self[infoName]["nodes"] = [AbsoluteNode(i) for i in nodes]


	def reapplyData(self, infoName, infoType="all", **kwargs):
		"""retrieve saved info AND APPLY IT """
		#print("memory reapplyData infoName {}, infoType {}".format(infoName, infoType))
		if not infoType in self.infoKinds and infoType != "all":
			raise RuntimeError("infoType {} is not recognised".format(infoType))
		if infoType == "all":
			for i in self.cellInfoTypes(infoName):
				self.reapplyData(infoName, infoType=i)
		else:
			self._applyInfo(infoName, infoType,
			                target=self.nodesFromInfoName(infoName),
			                **kwargs)

	def refresh(self, infoName="", infoType="", *args, **kwargs):
		"""updates existing memory with info from scene
		DOES NOT create new info if none exists"""

		gatheredGoss = [self._gatherInfo(infoType, target=i)
		                for i in self.nodesFromInfoName(infoName)]
		self[infoName][infoType] = gatheredGoss




	def _gatherInfo(self, infoType, target=None, **kwargs):
		"""implements specific methods of gathering information from scene
		"""
		target = AbsoluteNode(target)
		print(InfoTypes)
		print(InfoTypes._value2member_map_)
		print(InfoTypes._member_map_)
		if infoType not in InfoTypes and not \
				InfoTypes._value2member_map_.get(
					(infoType, )
				):
			raise RuntimeError("cannot gather info of type {}".format(infoType))
		if not cmds.objExists(target):
			raise RuntimeError("no object found named {}".format(target))

		if isinstance(infoType, str):
			infoType = InfoTypes._value2member_map_[
				(infoType, ) ]

		gatherFns = {
			InfoTypes.Attr : self._gatherAttrInfo,
			InfoTypes.Xform : self._gatherXformInfo,
			InfoTypes.Weight : self.getWeightInfo,
			InfoTypes.Shape : self.getShapeInfo,
		}

		returnDict = gatherFns[infoType](target, **kwargs)
		print("gatherInfo result")
		print(returnDict)

		return returnDict


	def _gatherAttrInfo(self, target, **kwargs):
		returnDict = {}
		# check if transform attributes are specifically requested
		baseList = cmds.listAttr(target, keyable=1)
		omitList = ["translate", "rotate", "scale"]
		outList = []

		if kwargs.get("xformAttrs"):
			omitList = []
		for i in baseList:
			if any([n in i for n in omitList]):
				continue
			outList.append(i)
		for i in outList:
			returnDict[i] = attr.getAttr(target + "." + i)
		return returnDict

	def _gatherXformInfo(self, target, **kwargs):
		returnDict = {}
		# speed is not yet of the essence
		for space, truth in zip(["world", "local"], (True, False)):
			spaceDict = {
				"translate": cmds.xform(target, q=True, ws=truth, t=True),
				"rotate": cmds.xform(target, q=True, ws=truth, ro=True),
				"scale": cmds.xform(target, q=True, ws=truth, s=True),
			}
			returnDict[space] = spaceDict
		if kwargs.get("jointMode"):
			for ax in "XYZ":
				jointOrient = cmds.getAttr(target + ".jointOrient" + ax)
				returnDict["jointOrient" + ax] = jointOrient
			returnDict["rotateOrder"] = cmds.getAttr(target + ".rotateOrder")

		if kwargs.get("relative"):
			"""still not sure of the best way to handle this"""
			mat = transform.MMatrixFromPlug(kwargs["relative"])
		return returnDict

	def getWeightInfo(self, target, targetAttr=None, **kwargs):
		return {}



	def _applyInfo(self, infoName, infoType, target=None,
	               relative=None, **kwargs):

		# test view all data
		#print(self.data.serialise(pretty=True))
		pprint.pprint(self.data.serialise())

		allInfo = self[infoName]

		# print(("allInfo {}".format(allInfo)))
		# print(("target {}".format(target)))

		space = kwargs.get("space") or "world"

		if not isinstance(target, list):
			#print("converting from list")
			index = self.indexFromNode(infoName, target)
			info = [allInfo[infoType][index]]
			target = [target]
		else:
			info = allInfo[infoType]


		print("info to apply is {}".format(info))
		# it's really, really for the best if you just work by sequence
		for target, info in zip(target, info):
			print(("target {}, info {}".format(target, info)))


			if not cmds.objExists(target):
				raise RuntimeError("APPLYINFO TARGET {} DOES NOT EXIST".format(target))
			if infoType == "attr":
				for k, v in info.items():
					#print "setting attr {}.{} to {}".format(target, k, v)
					try:
						attr.setAttr(target + "." + k, v)
					except Exception as e:
						print(("could not remember attr {}, value {}".format(k, v)))

			elif infoType == "xform":
				info = info[space]
				cmds.xform(target, ws=True, t=(info["translate"]))
				cmds.xform(target, ws=True, ro=info["rotate"])
				cmds.xform(target, ws=True, s=info["scale"])

			elif infoType == "weight":
				# nope
				pass

			elif infoType == "shape":
				self.setShapeInfo(info, target=target)
				pass

	def indexFromNode(self, infoName, node):
		return self[infoName]["nodes"].index(node)

	def nodesFromInfoName(self, infoName):
		"""returns list of all nodes tracked by infoName"""
		return [AbsoluteNode(i) for i in self[infoName]["nodes"]]


	def setNodes(self, infoName, nodes):
		if not isinstance(nodes, list):
			nodes = [nodes]
		self[infoName]["nodes"] = [AbsoluteNode(i)() for i in nodes ]

	def getFlattenedNodes(self):
		"""ensure nodes are stored as strings, not AbsNodes"""
		#self.nodes = [str(i) for i in self.nodes] # for some reason | characters screw up strings
		return [str(i) for i in self.nodes]

	@staticmethod
	def makeBlankInfoType(infoType):
		"""in case special types need special templates"""
		typeDict = {
			"attr": [],
			"xform": [{"local" : [], # ARRAY OF STRUCTS
			          "world" : []}],  # YOU HAVE NO POWER HERE
			"weight": [],
			"shape": [],
		}

		return typeDict[infoType]

	def setClosed(self, infoName, infoType=None, status=True):
		"""prevent a memory infotype or whole cell from being refreshed"""
		return # more trouble than worth
		self._allocateTypeCell(infoName, infoType)
		if infoType:
			self[infoName][infoType]["CLOSED"] = status
		else:
			self[infoName]["CLOSED"] = status

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
			print ("shape regen failed for some reason, likely mismatch in "
			       "shapeType - try refreshing")
			return


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

	def serialise(self):
		#print("serialise nodes {}".format(self["nodes"]))
		#self["nodes"] = [ str(i) for i in self.get("nodes") or []]
		return self.data.serialise()

	def display(self):
		return pprint.pformat(self.serialise())

"""


"""



