""" wip refit of memory to inherit directly from abstractTree"""

import copy
from edRig import cmds, om, ECA, AbsoluteNode
from edRig import attr, transform, curve, mesh, surface
from edRig.lib.python import AbstractTree


class Memory2(AbstractTree):
	""" a long time ago Matt Goutte told me that trees are all you need
	in cg """
	infoKinds = ["attr", "xform", "weight", "shape", "multi"]

	def __init__(self, name="memory", val=None):
		super(Memory2, self).__init__(name, val)
		self["nodes"] = [] # node storage

	""" a top-level tree interface is all that's necessary - 
	no need for a full tree object to hold an integer value """

	@property
	def nodes(self):
		""":rtype list(AbsoluteNode)"""
		return self["nodes"]
	@nodes.setter
	def nodes(self, val):
		self["nodes"] = val

	IGNORE_KEYS = ("nodes", )

	def _allocateSpace(self, infoName, nodes=None):
		"""creates blank memory dict
		"""

		if self.get(infoName):
			return

		self[infoName] = {}
		#self[infoName]["CLOSED"] = False
		self[infoName]["nodes"] = nodes
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
		return self.keys()

	def infoTypes(self, infoName):
		return self[infoName].keys()

	def _initialiseCell(self, infoName, infoType, nodes=None):
		if not infoName in self.infoNames():
			print "allocating blank space for infoName {}".format(infoName)
			self._allocateSpace(infoName, nodes=nodes)

		if not infoType in self[infoName].keys():
			#print "gathering goss, making blank info"
			self[infoName][infoType] = self.makeBlankInfoType(
				infoType)

	def remember(self, infoName, infoType, nodes=None, **kwargs):
		"""add information to op's memory if none exists
		we remember lists here
		main entrypoint"""
		print("remember infoName {}, infotype {}, nodes {}".format(
			infoName, infoType, nodes)
		)

		# multi memory support
		if isinstance(infoType, list):
			for i in infoType:
				self.remember(infoName, i, nodes)

		if not isinstance(nodes, list):
			nodes = [nodes]

		self._initialiseCell(infoName, infoType, nodes=nodes)

		if not self[infoName][infoType]:

			# pre-existing information will not be lost, nodes will still be refreshed

			gatheredGoss = [self._gatherInfo(infoType, target=i, **kwargs) for i in nodes]
			self[infoName][infoType] = gatheredGoss

		# only store NAMES of nodes
		self[infoName]["nodes"] = [AbsoluteNode(i)() for i in nodes]


	def recall(self, infoName, infoType="all", **kwargs):
		"""retrieve saved info AND APPLY IT """
		print("memory recall infoName {}, infoType {}".format(infoName, infoType))
		if not infoType in self.infoKinds and infoType != "all":
			raise RuntimeError("infoType {} is not recognised".format(infoType))
		if infoType == "all":

			for i in self.infoKinds:
				self.recall(infoName, infoType=i)
		else:
			# return self[infoName][infoType]
			self._applyInfo(infoName, infoType,
			                target=self.nodesFromInfoName(infoName),
			                **kwargs)

	def refresh(self, infoName="", infoType="", *args, **kwargs):
		"""updates existing memory with info from scene
		DOES NOT create new info if none exists"""
		print("memory refresh - nodesFromInfoName {} are {}".format(
			infoName, self.nodesFromInfoName(infoName)) )
		gatheredGoss = [self._gatherInfo(infoType, target=i)
		                for i in self.nodesFromInfoName(infoName)]
		self[infoName][infoType] = gatheredGoss
		# print( "{}-{} is now {}".format(infoName, infoType,
		#                                self[infoName][infoType]) )

	def remove(self, infoName, infoType=None):
		"""clears memory selectively without going into the datafile
		take note FS"""
		if infoType:
			self[infoName].pop(infoType, None)
		else:
			self.pop(infoName, None)

	def renewableMemory(self):
		"""returns all memory slots that have a value - eg that
		can be renewed from scene"""
		print("renewable memory")
		print(self.display())
		returnDict = {}
		for i in self.branches:
			print("i branch {} value {}".format(i.name, i.value))
			if not isinstance(i.value, dict):
				continue
			if i.name == "nodes":
				continue
			if i.get("closed"):
				continue
			returnDict[i.name] = []
			print("i branches {}".format(i.branches))
			for n in i.value.keys():
				print("n branch {}".format(n))
				if n == "nodes" or n== "closed":
					continue
				returnDict[i.name].append(n)

		return returnDict

	def _gatherInfo(self, infoType, target=None, **kwargs):
		"""implements specific methods of gathering information from scene
		"""
		target = AbsoluteNode(target)
		if infoType not in self.infoKinds:
			raise RuntimeError("cannot gather info of type {}".format(infoType))
		if not cmds.objExists(target):
			raise RuntimeError("no object found named {}".format(target))

		# print ""
		# print "GATHERING GOSS"

		""" IMPLEMENT RELATIVE VS ABOLUTE 
		gather both - apply only one as per state of node"""

		returnDict = {}
		attrList = []

		# print("infotype {}".format(infoType))
		# print("target {}".format(target))
		# print("kwargs {}".format(kwargs))

		if infoType == "attr":

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


		elif infoType == "xform":
			# speed is not yet of the essence
			for space, truth in zip(["world", "local"], (True, False)):
				spaceDict = {
					"translate" : cmds.xform(target, q=True, ws=truth, t=True),
					"rotate" : cmds.xform(target, q=True, ws=truth, ro=True),
					"scale" : cmds.xform(target, q=True, ws=truth, s=True),
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
				pass



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

		# test view all data
		#print(self.serialise(pretty=True))

		allInfo = self[infoName]

		#print("allInfo {}".format(allInfo))
		#print("target {}".format(target))

		space = kwargs.get("space") or "world"

		if not isinstance(target, list):
			#print("converting from list")
			index = self.indexFromNode(infoName, target)
			info = [allInfo[infoType][index]]
			target = [target]
		else:
			info = allInfo[infoType]


		# print("allInfo {}".format(allInfo))
		# print("target {}".format(target))

		# if infoType == "xform" :
		# 	info = info[space]

		# print("target {}".format(target))
		# print("info {}".format(info))

		#print "info to apply is {}".format(info)
		# it's really, really for the best if you just work by sequence
		for target, info in zip(target, info):
			#print("target {}, info {}".format(target, info))


			if not cmds.objExists(target):
				raise RuntimeError("APPLYINFO TARGET {} DOES NOT EXIST".format(target))
			if infoType == "attr":
				for k, v in info.iteritems():
					#print "setting attr {}.{} to {}".format(target, k, v)
					try:
						attr.setAttr(target + "." + k, v)
					except Exception as e:
						print("could not remember attr {}, value {}".format(k, v))

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
		# return {infoType : typeDict[infoType],
		# 		#"CLOSED" : False,
		#         }
		return typeDict[infoType]

	def setClosed(self, infoName, infoType=None, status=True):
		"""prevent a memory infotype or whole cell from being refreshed"""
		return # more trouble than worth
		self._initialiseCell(infoName, infoType)
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
		self.nodes = [ str(i) for i in self.nodes]
		return super(Memory2, self).serialise()

