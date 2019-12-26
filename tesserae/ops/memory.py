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

	@property
	def nodes(self):
		""":rtype list(AbsoluteNode)"""
		return self["nodes"]
	@nodes.setter
	def nodes(self, val):
		self["nodes"] = val

	#
	def __getitem__(self, key):
		return super(Memory2, self).__getitem__(key)

	def __setitem__(self, key, value):
		super(Memory2, self).__setitem__(key, value)

	def _allocateSpace(self, infoName, nodes=None):
		"""creates blank memory dict
		one memory cell per node"""

		self[infoName] = {}
		self[infoName]["CLOSED"] = False
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
			self[infoName][infoType] = self.makeBlankInfoType(
				infoType)

			# pre-existing information will not be lost, nodes will still be refreshed

			gatheredGoss = [self._gatherInfo(infoType, target=i, **kwargs) for i in nodes]
			self._storage[infoName][infoType] = gatheredGoss
		# always set node regardless to ensure info is relevant in scene
		# self.setNode(infoName, core.AbsoluteNode(node))
		self._storage[infoName]["nodes"] = [AbsoluteNode(i) for i in nodes]


	def recall(self, infoName, infoType="all", **kwargs):
		"""retrieve saved info AND APPLY IT """
		if not infoType in self.infoKinds and infoType != "all":
			raise RuntimeError("infoType {} is not recognised".format(infoType))
		if infoType == "all":
			# returnDict = {}
			# returnDict.clear()
			for i in self.infoKinds:
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

		""" IMPLEMENT RELATIVE VS ABOLUTE 
		gather both - apply only one as per state of node"""

		returnDict = {}
		target = AbsoluteNode(target)  # speed
		attrList = []
		if infoType == "attr":
			# gather dict of attribute names and values
			# all of them?
			if kwargs.get("allAttrs"):
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
		self.nodes = [AbsoluteNode(i) for i in self.nodes]
		for k, v in self._storage.iteritems():
			print "k is {}, v is {}, v keys are {}".format(k, v, v.keys())
			if "nodes" in v.keys():
				v["nodes"] = [AbsoluteNode(i) for i in v["nodes"]]
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
