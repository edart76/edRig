# ops to be main stages, able to be blended in a control chain
import edRig.pipeline
from edRig.tesserae.ops.op import Op
from edRig import core, attrio, utils, transform, control, beauty

#from edRig.tesserae.ops.memory import Memory2
from edRig.structures import ActionItem
import functools, inspect
import copy
import pprint
from collections import OrderedDict

class LayerOp(Op):
	"""base class for sequential operations that make up a rig
	merge back into base op, there's no point keeping them separate yet"""

	outputs = {}
	extras = {}  # use with caution
	GPUable = False
	# use to chain surface deformers directly



	def __init__(self, *args, **kwargs):
		super(LayerOp, self).__init__(*args, **kwargs)
		print "layer sync is {}".format(self.sync)
		self.controller = None

		self.saveData = None
		self.dataFileExists = False


	@property
	def memory(self):
		""" looks up memory from abstract's data
		:rtype Memory2"""
		return self.data("memory")


	def renameOp(self, newName, renameData=False):
		"""old stuff about data can be managed at graph"""
		if self.abstract:
			self.opName = newName
		else:
			newDataPath = attrio.dataFolder + newName
			oldDataPath = self.dataFilePath
			self.opName = newName
			# check if data exists already
			if renameData and not edRig.pipeline.checkJsonFileExists(newDataPath):
				attrio.renameFile(old=oldDataPath, new=newDataPath)
			else:
				self.checkDataFileExists()

	@property
	def dataFilePath(self):
		# one file per op
		if self.abstract:
			path = self.abstract.dataPath
		else:
			path = attrio.dataFolder + self.opName # in the past
		# self.checkDataFileExists(path)
		return path

	def checkDataFileExists(self):
		if self.abstract:
			return True
		if edRig.pipeline.checkJsonFileExists(self.dataFilePath):
			print "data file for {} exists".format(self.opName)
			self.dataFileExists = True
		else:
			print "data file for {} does not exist, making new one".format(self.opName)
			edRig.pipeline.makeBlankFile(path=self.dataFilePath)
			self.dataFileExists = True

	def setAbstract(self, abstract, inDict=None, outDict=None, define=True):
		super(LayerOp, self).setAbstract(abstract, inDict, outDict, define)

	def memoryActions(self):
		openDict = self.memory.renewableMemory()

		returnDict = OrderedDict()
		# add "all" options
		if len(openDict.keys()) > 1:
			returnDict["all"] = ActionItem(
				{"func" : self.refreshAllMemory}, name="all")
		for k,v in openDict.iteritems():
			returnDict[k] = {}

			for i in v:
				returnDict[k][i] = ActionItem({
					#"func" : self.memory.refresh,
					"func" : self.refreshMemoryAndSave,
					"kwargs" : {
						"infoName" : k,
						"infoType" : i,
					} }, name=i )

		return returnDict

	def refreshMemoryAndSave(self, infoName=None, infoType=None):
		"""save out memory with every refresh"""
		self.memory.refresh(infoName=infoName, infoType=infoType)
		#self.saveOutMemory()

	def refreshAllMemory(self):
		"""refreshes all open memory cells"""
		for k, v in self.memory.renewableMemory().iteritems():
			for i in v:
				self.memory.refresh(infoName=k, infoType=i)
		#self.saveOutMemory()

	def remember(self, infoName=None, infoType=None, nodes=None,
	             relative=None, **kwargs):
		"""apply saved data if it exists, create it if not
		"""

		# support for custom memory behaviour for complex types
		if isinstance(infoType, control.Control):
			return self.remember( infoName, compound=infoType.memoryInfo())

		# support for remembering compound data
		if kwargs.get("compound"):
			"""we expect dict of 
			{"infoName" : {"infoType" : ["attr", "xform"],
							"nodes" : [nodes] },
				"otherInfoName" : {etc} }
			"""
			for k, v in kwargs.pop("compound").iteritems():
				self.remember(infoName=k,
				              infoType=v["infoType"],
				              nodes=v["nodes"],
				              relative=v.get("relative"),
				              **kwargs)
			return True

		# check over nodes to make sure they're all valid
		# not sure the best way to do this
		nodes = [i for i in nodes if i]

		if isinstance(infoType, (list, tuple)):
			for i in infoType:
				self.remember(infoName, i, nodes, relative, **kwargs)
			return True

		"""relative left None to ignore - otherwise specify transform or matrix
		plug to remember and recall only in local space
		actually any kind of plug, corresponding to the value being recalled"""

		if infoName in self.memory.infoNames():
			if infoType in self.memory.infoTypes(infoName):
				# print ""
				# print "RECALLING from remember"
				self.memory.setNodes(infoName, nodes)
				self.memory.recall(infoName, infoType, **kwargs)
			else:
				self.log("infoType {} not found in memory {}".format(infoType,
				                                                  self.memory.infoTypes(infoName)) )

		else:
			self.log( "infoName {} not found in memory {}".format(infoName,
			                                                  self.memory.infoNames()) )
		self.memory.remember(infoName, infoType, nodes, **kwargs)


	def getAllActions(self):
		"""super call freaks out for some reason with regen'd objects
		no it freaked out because reloading edRig deleted all system modules"""
		base = {}
		base = super(LayerOp, self).getAllActions()

		try:
			base.update({"memory": self.memoryActions()})
		except Exception as e:
			print "memory actions error"
			print "error is {}".format(e)
		return base

	# convenience and standardisation
	def makeStarter(self, name=None, d="0D"):
		"""makes a starting object, adds it to memory"""
		name = name or self.opName
		if d == "0D":
			start = self.ECA("locator", name+"_starter_"+d)
			self.remember(infoName=name, infoType="xform", nodes=start)
		elif d == "1D":
			start = self.ECA("nurbsCurve", name+"_starter_"+d).shape
			self.remember(infoName=name, infoType="shape", nodes=start)
		return start

	def constrainToInput(self, inputName=None, plug=None,
	                     target=None, closestPoint=None):
		"""get point using recalled base position"""
		sourcePlug = self.getInput(inputName).plug if inputName \
			else plug
		basePlug = utils.getMatrixPlugFromPlug(
			fromPlug=sourcePlug,
			closestPoint=closestPoint)
		transform.decomposeMatrixPlug(basePlug, target=target)

	def addControl(self, ctrl=None):
		"""wrapper for organising control object properly within op
		 :param ctrl : control.Control"""
		self.showGuidesStack.append( ctrl.showGuides )
		self.hideGuidesStack.append( ctrl.hideGuides )

		for i in ctrl.layers:
			self.addToSet()

	def markAsGuide(self, target):
		""" turns stuff yellow """
		beauty.setColour(target, beauty.colourPresets["guides"])


	# serialisation and regeneration
	def serialise(self):
		orig = super(LayerOp, self).serialise()
		return orig

	@classmethod
	def fromDict(cls, regenDict, abstract=None):
		opInstance = Op.fromDict(regenDict, abstract)

		return opInstance

