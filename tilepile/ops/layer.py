# ops to be main stages, able to be blended in a control chain
from edRig.tilepile.ops.op import Op
from edRig import core, attrio
from edRig.layers.setups import Memory, OpAttrItem
from edRig.structures import ActionItem
import functools, inspect
import copy
import pprint
from collections import OrderedDict

class LayerOp(Op):
	"""base class for sequential operations that make up a rig"""

	outputs = {}
	extras = {}  # use with caution
	GPUable = False
	# use to chain surface deformers directly



	def __init__(self, *args, **kwargs):
		super(LayerOp, self).__init__(*args, **kwargs)
		print "layer sync is {}".format(self.sync)
		self.controller = None
		self.memory = Memory()
		# self.loadMemory()

		self.saveData = None
		self.dataFileExists = False
		# print "checking dataFileExists"
		# self.checkDataFileExists()


	def renameOp(self, newName, renameData=False):
		"""old stuff about data can be managed at graph"""
		if self.abstract:
			self.opName = newName
		else:
			newDataPath = attrio.dataFolder + newName
			oldDataPath = self.dataFilePath
			self.opName = newName
			# check if data exists already
			if renameData and not attrio.checkFileExists(newDataPath):
				attrio.renameFile(old=oldDataPath, new=newDataPath)
			else:
				self.checkDataFileExists()

	# def plan(self):
	# 	kSuccess = super(LayerOp, self).plan()
	# 	self.loadMemory()
	#
	# def build(self):
	# 	kSuccess = super(LayerOp, self).build()
	# 	self.loadMemory()


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
		if attrio.checkFileExists(self.dataFilePath):
			print "data file for {} exists".format(self.opName)
			self.dataFileExists = True
		else:
			print "data file for {} does not exist, making new one".format(self.opName)
			attrio.makeBlankFile(path=self.dataFilePath)
			self.dataFileExists = True

	def setAbstract(self, abstract, inDict=None, outDict=None, define=True):
		super(LayerOp, self).setAbstract(abstract, inDict, outDict, define)
		# patch methods
		self.__dict__["saveOutData"] = self.abstract.saveOutData
		self.__dict__["searchData"] = self.abstract.searchData
		self.loadMemory()

		#self.checkDataFileExists()

	def saveOutMemory(self):
		self.saveOutData(infoName="memory", data=self.memory.serialiseMemory())
		# attrio.updateData("memory", self.memory.serialiseMemory(),
		#                   path=self.dataFilePath)

	def loadMemory(self):
		#goss = attrio.getData("memory", self.dataFilePath)
		goss = self.searchData("memory")
		print "loaded memory is {}".format(goss)
		self.memory.reconstructMemory(goss)

	def memoryActions(self):
		openDict = self.memory.renewableMemory()
		#print "op openDict is {}".format(openDict) # add proper list support here
		#print "op memory is {}".format(pprint.pformat(self.memory))
		#pprint.pprint(self.memory, indent=3)
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
		self.saveOutMemory()

	def refreshAllMemory(self):
		"""refreshes all open memory cells"""
		for k, v in self.memory.renewableMemory().iteritems():
			for i in v:
				self.memory.refresh(infoName=k, infoType=i)
		self.saveOutMemory()

	def remember(self, infoName=None, infoType=None, nodes=None, **kwargs):
		"""apply saved data if it exists, create it if not
		just a bit of recreational industrial espionage"""

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
				              **kwargs)
				return True

		if infoName in self.memory.infoNames():
			if infoType in self.memory.infoTypes(infoName):
				print ""
				print "RECALLING from remember"
				self.memory.setNodes(infoName, nodes)
				self.memory.recall(infoName, infoType, **kwargs)
			else:
				print "infoType {} not found in memory {}".format(infoType,
				                                                  self.memory.infoTypes(infoName))
		else:
			print "infoName {} not found in memory {}".format(infoName,
			                                                  self.memory.infoNames())
		# self.memory.setNodes(infoName, nodes)
		self.memory.remember(infoName, infoType, nodes, **kwargs)



	"""EVENTUALLY make this a live link, so every time something is read from
	memory object, it's read from the file, and vice versa
	or only update files at start and end of build process"""

	def getAllActions(self):
		"""super call freaks out for some reason with regen'd objects"""
		base = {}
		try:
			# print "type type self is {}".format(type(type(self))) # returns type
			base = super(LayerOp, self).getAllActions()

		except Exception as e:
			print "super call experienced error"
			print "error is {}".format(e)

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

	# serialisation and regeneration
	def serialise(self):
		orig = super(LayerOp, self).serialise()
		orig["memory"] = self.memory.serialiseMemory()

		return orig

	@classmethod
	def fromDict(cls, regenDict, abstract=None):
		print "layerOpFromDict"
		print "regendict is {}".format(regenDict)
		opInstance = Op.fromDict(regenDict, abstract)
		#opInstance = Op.fromDict()
		if "memory" in regenDict.keys():
			print "regen memory"
			#opInstance.memory.reconstructMemory({"memory" : copy.deepcopy(regenDict["memory"])})
			opInstance.memory.reconstructMemory(regenDict["memory"])
			print "done"

		return opInstance

