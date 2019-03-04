# # define base class for layers, and main interaction with tilepile
# from edRig import core, curve, control, attrio
# from edRig.core import Op
# from edRig.layers.setups import Memory, OpAttrItem
# from edRig.layers.action import ActionItem
# #from edRig.tilepile
# from maya import cmds
# import maya.api.OpenMaya as om
# import edRig
#
# import time, datetime, importlib, copy
#
# dataFolder = "F:/all projects desktop/common/edCode/edRig/data/"
#
#
# class CommonSettings(object):
# 	"""general container for any common settings
# 	across a full rig build"""
#
# 	def __init__(self):
# 		print "CommonSettings initialised"
# 		self.step = None  # plan, build, run, maybe more?
#
#
# class PermanentOp(Op):
# 	"""for ops that need to stick around
# 	each rig will have these, and will need to be merged back
# 	when imported as components"""
#
# 	def __init__(self):
# 		core.Op.__init__(self)
#
# 	def mergeToMaster(self):
# 		"""for all attributes, replace with master's
# 		for all nodes, maybe reconnect, but otherwise just
# 		change references"""
#
#
# class TimeControl(PermanentOp):
# 	""" *slow mo guys music*
# 	root system for managing time in a maya scene,
# 	or outside it"""
#
# 	def __init__(self):
# 		PermanentOp.__init__(self)
# 		if not self.checkUnique():
# 			return
#
# 		self.setup()
#
# 	def setup(self):
# 		self._mayaTime = "time1"
# 		self.control = self.ECA("transform", "timeControl")
# 		# cmds.addAttr(self.control, ln="time")
# 		# cmds.addAttr(self.control, ln="startFrame", at="int")
# 		# cmds.addAttr(self.control, ln="endFrame", at="int")
# 		#
# 		# cmds.connectAttr(self._mayaTime+".outTime", self.control+".time")
#
# 	# stop
# 	@property
# 	def mayaTime(self):
# 		return self.control + ".time"
#
# 	def checkUnique(self):
# 		return True
#
# 	@property
# 	def currentTime(self):
# 		return datetime.datetime.now()
#
# 	@property
# 	def preciseTime(self):
# 		return time.now()
#
#
# #class RIG_CONTROLLER(object):
# 	"""so powerful it breaks naming convention
# 	this is what queues up and manages all sequential operations
# 	that make up a rig, including pausing, restarting etc"""
#
# 	character = None
# 	version = 1
# 	opGraph = {}
# 	# here we will build an internal graph mirroring (informing) the UI
# 	"""{
# 		eyyy.JointCurveOp : {
# 			"op" : op object,
# 			"inputs" : inputs,
# 			"outputs" : outputs,
# 			"data" : data,
# 			"index" : whoKnows
# 			},
# 		yo.LimbOp : {
# 			etc
# 		}
# 	}"""
# 	environment = None
# 	settings = None
# 	stepName = None
# 	stepIndex = None
# 	# step sequence - if necessary add more here
# 	stepList = ["plan", "build", "run"]
#
# 	def __init__(self, character="testCharacter", step=None):
# 		self.character = character
# 		print "assuming direct control of {}".format(character)
#
# 		self.settings = CommonSettings()
# 		if step:
# 			self.stepIndex = self.indexFromStepName(step)
#
# 		self.rigPath = "{}{}_v{}".format(dataFolder, self.character, self.version)
#
# 	def indexFromStepName(self, stepName):
# 		if stepName not in str(self.stepList):
# 			raise RuntimeError("{} is not a valid step you moron".format(stepName))
# 		index = self.stepList.index(stepName)
# 		self.stepIndex = index
# 		print "self.stepIndex is {}".format(self.stepIndex)
#
# 	def rigItLikeYouDigIt(self):
# 		"""hold on to ya butts"""
#
# 		if self.stepIndex is None:
# 			self.stepIndex = self.indexFromStepName(self.stepName)
# 		print "ops to execute are {}".format(self.opGraph)
# 		numOps = len(self.opGraph.keys())
# 		self.execOrder = [None] * numOps
#
# 		# all ops will now be properly ordered
# 		self.determineIndices()
#
# 		for i in self.opGraph.values():
# 			# opIndex = self.opGraph[i]["index"]
# 			print "i in opGraph values is {}".format(i)
# 			opIndex = i["index"] - 1
# 			self.execOrder[opIndex] = i
# 			print "execOrder is {}".format(self.execOrder)
# 		# internal opgraph dictionaries are now in order
#
# 		for i in self.execOrder:
# 			print "i in execOrder is {}".format(i)
# 			kSuccess = i["op"].plan()
# 			if self.stepIndex == 0:
# 				kSuccess = i["op"].onPlanStop()
# 			if kSuccess:
# 				print "all according to kSuccess"
# 			else:
# 				raise RuntimeError("NOT ACCORDING TO KSUCCESS")
#
# 			kSuccess = i["op"].run()
# 			if kSuccess:
# 				print "all according to kSuccess"
# 			else:
# 				raise RuntimeError("NOT ACCORDING TO KSUCCESS")
# 		print "please welcome your new child with kindness"
#
# 	def setCommonSettings(self, settings):
# 		"""expects a CommonSettings object"""
# 		self.settings = settings
#
# 	def getAllopNames(self):
# 		return self.opGraph.keys()
#
# 	def getAllOpEntries(self):
# 		return self.opGraph.values()
#
# 	def getAllOps(self):
# 		return [i["op"] for i in self.getAllOpEntries()]
#
# 	def addOp(self, op):
# 		"""adds an op to the controller execution order"""
# 		print ""
# 		print "adding op {} to controller".format(op)
# 		# make sure op name is unique
# 		self.renameOp(op=op, newName=op.opName)
#
# 		#if op.__name__ in self.opGraph.keys():
# 		if self.opFromOpName(op.opName):
# 			print "op {} is already known to the CONTROLLER".format(op)
# 			return
# 		op.controller = self
# 		opDict = {
# 			"op": op,
# 			"index": None,  # to be determined at build time
# 			"builtStep": None,
# 			"opName": op.opName
# 		}
# 		#cry havoc
# 		self.opGraph[op.opName] = opDict
# 		print ""
#
# 	def removeOp(self, op=None, opName=None):
# 		if op:
# 			opName = op.opName
# 		op = self.opFromOpName(opName)
# 		test = self.getOpsFedByOutputs(op)
# 		print "test is {}".format(test)
# 		for k, v in self.getOpsFedByOutputs(op).iteritems():
# 			for n in v:
# 				print "k is {}, v is {}, n is {}".format(k, v, n)
# 				self.disconnectOutputObjectFromInput(
# 					outOp=op, outAttrName=k,
# 					inOp=n[0], inAttr=n[1])
# 		for k, v in self.getOpsFeedingInputs(op):
# 			for n in v:
# 				self.disconnectOutputObjectFromInput(
# 					outOp=n[0], outAttr=n[1],
# 					inOp=op, inAttrName=k)
# 		print "successfully disconnected op {}".format(opName)
#
# 		self.opGraph.pop(opName)
# 		print "successfully removed op"
#
# 	def getOpsFedByOutputs(self, targetOp):
# 		"""returns all attrs and ops fed by targetOp's outputs"""
# 		returnDict = {}
# 		for i in targetOp.outputRoot.getAllConnectable():
# 			cons = []
# 			for n in i.getConnections():
# 				fedOp = self.opFromOpName(n["opName"])
# 				fedAttr = n["attr"]
# 				cons.append( (fedOp, fedAttr) )
# 			returnDict[i.name] = cons
# 		return returnDict
#
# 	def getOpsFeedingInputs(self, targetOp):
# 		"""returns all ops and attrs feeding targetOp's inputs"""
# 		returnDict = {}
# 		for i in targetOp.inputRoot.getAllConnectable():
# 			cons = []
# 			for n in  i.getConnections():
# 				feedingOp = self.opFromOpName(n["opName"])
# 				feedingAttr = n["attr"]
# 				cons.append( (feedingOp, feedingAttr) )
# 			returnDict[i.name] = cons
# 		return returnDict
#
#
# 	def updateOp(self, op):
# 		"""updates op if known to controller, adds it if not"""
# 		if op.opName not in self.opGraph.keys():
# 			self.addOp(op)
# 		if op.opName in self.opGraph.keys():
# 			# self.opGraph[op.__name__]["inputs"].update(op.inputs)
# 			# self.opGraph[op.__name__]["outputs"].update(op.outputs)
# 			# self.opGraph[op.__name__]["data"].update(op.data)
# 			self.opGraph[op.op.opName]["op"] = op
# 			pass
#
# 	@staticmethod
# 	def connectOutputObjectToInput(outOp=None, outAttrName=None,
# 	                               inOp=None, inAttrName=None,
# 	                               outAttrItem=None, inAttrItem=None):
# 		#print "outAttrName is {}".format(outAttrName)
# 		outAttr = outAttrItem or outOp.getOutput(outAttrName)
# 		inAttr = inAttrItem or inOp.getInput(inAttrName)
# 		#
# 		# print "outAttr is {}".format(outAttr)
# 		# print "inAttr is {}".format(inAttr)
# 		inAttr.connections = [{"opName" : outOp.opName,
# 		                      "attr" : outAttr}]
#
# 		outAttr.connections.append( {"opName" : inOp.opName,
# 		                             "attr" : inAttr} )
#
# 	@staticmethod
# 	def disconnectOutputObjectFromInput(outOp=None, outOpName=None, outAttrName=None,
# 	                                    inOp=None,inOpName=None, inAttrName=None,
# 	                                    outAttr=None, inAttr=None):
# 		outAttr = outAttr or outOp.getOutput(outAttrName)
# 		inAttr = inAttr or inOp.getInput(inAttrName)
# 		newCons = [i for i in outAttr.connections if i["attr"] != inAttr]
# 		outAttr.connections = newCons
# 		newInCons = [i for i in inAttr.connections if i["attr"] != outAttr]
# 		inAttr.connections = newInCons
#
# 	def checkConnections(self, outOp=None, outOpName=None, outAttrName=None,
# 	                     inOp=None, inOpName=None, inAttrName=None):
# 		"""checks that attributes still exist; reset connections if not
# 		it's easier to do this based on op, and just call it on each at runtime"""
# 		if outOp:
# 			if not isinstance(outOp, Op):
# 				outOp = self.opGraph[outOp]["op"]
#
# 		outAttr = outOp.getOutput(outAttrName) if outAttrName else None
# 		for i in outAttr.getConnections():
# 			newInAttr = i["attr"]
# 			newInOp = i["op"]
# 			if newInAttr not in newInOp.inputs:
# 				outAttr.connections.remove(i)
#
# 		if inOp:
# 			if not isinstance(inOp, Op):
# 				inOp = self.opGraph[inOp.opName]["op"]
# 		inOp = inOp or self.opGraph[inOpName]["op"]
# 		inAttr = inOp.getinput(inAttrName) if inAttrName else None
# 		if inAttr.connections[0]["attr"] not in outOp.outputs:
# 			inAttr.connections = []
#
#
# 	@staticmethod
# 	def propagateOutputObjectInfo(op):
# 		for i in op.outputRoot.getAllConnectable():
# 			for n in i.getConnections():
# 				n["attr"].value = i.value
#
# 	def determineIndices(self):
# 		"""numbers ops perfectly and with no problems at all
# 		assume that an op with no input connections can be executed anytime,
# 		and others cannot be executed until all their inputs are complete"""
#
# 		# OPS CANNOT BE ASSIGNED AN INDEX UNTIL ALL THEIR INPUTS HAVE INDICES
# 		print ""
# 		print "DETERMINING INDICES"
# 		for i in self.getAllOpEntries():
# 			i["index"] = None
# 		index = 0
#
# 		for i in self.getAllOpEntries():
# 			# step order is assumed to be irrelevant, and graph is CORRECTLY
# 			# assumed to be acyclic
# 			op = i["op"]
# 			print "getting index for op {}".format(op.opName)
# 			index = self.determineIndex(op, index)
# 			print "determined index is {}".format(index)
#
# 	def determineIndex(self, op, index):
# 		# if it already has an index, skip it
# 		if self.opGraph[op.opName]["index"]:
# 			print "already found index {} for op {}".format(
# 				self.opGraph[op.opName]["index"], op.opName)
# 			print "returning original index {}".format(index)
# 			return index
#
# 		# if self.opGraph
# 		for i in op.getConnectedInputs(): # returns attr items
# 			print "op inputs is {}".format(op.inputs)
# 			connName = i.getConnections()[0]["opName"]
# 			connEntry = self.opGraph[connName]
# 			index = self.determineIndex(connEntry["op"], index)
#
# 		print "setting index of {} to {}".format(op.opName, index)
# 		self.opGraph[op.opName]["index"] = index
# 		index = index + 1
# 		return index
#
# 	"""
# 	so here's the juicy deet
# 	the internal graph is a record and a check - we don't need to keep going back to it
# 	on every propagation
# 	on saving the graph:
# 		update all ops in internal graph
# 		serialise graph to dict
# 	on loading the graph:
# 		load internal graph from dict
# 		create all ops according to keys
# 		restore all data
# 		reconnect all ops from dict
# 	"""
# 	#
# 	# @staticmethod
# 	# def isArray(attr):
# 	# 	return True if "valueList" in attr.keys() else False
#
# 	def clearRig(self):
# 		print "clearing rig"
# 		self.opGraph.clear()
#
# 	def serialiseRig(self):
# 		"""serialise saved opgraph to list"""
# 		print "serialiseRig"
# 		print "controller opGraph is {}".format(self.opGraph)
# 		opDictList = []
# 		for i in self.opGraph.keys():
# 			print "i is {}".format(self.opGraph[i])
# 			serialised = self.opGraph[i]["op"].serialise()
# 			print "serialised is {}".format(serialised)
# 			opDictList.append(serialised)
# 			print ""
# 		return opDictList
#
# 	def saveRig(self):
# 		# help
# 		opDictList = self.serialiseRig()
# 		attrio.ioinfo(name=self.character, mode="out",
# 		              info=opDictList, path=self.rigPath)
#
# 	def loadRig(self, path=None):
# 		return attrio.ioinfo(name=self.character, mode="in", path=path)
#
# 	def reconstructRig(self, opDictList=[], clear=True):
# 		# first look through and load all modules that need loading
# 		opDictList = [i for i in opDictList if i is not None]
# 		print "opDictList is {}".format(opDictList)
# 		moduleList = []  # loaded modules
#
# 		if clear:
# 			self.opGraph.clear()
#
# 		for i in opDictList:
# 			loadedModule = self.safeLoadModule(i["MODULE"])
# 			newOp = self.reconstructOp(info=i, module=loadedModule)
# 			print "newOp is {}".format(newOp)
# 			if newOp:
# 				self.addOp(newOp)
#
# 		# now reconnect all ops
#
# 		# reconnect attributes
# 		for i in self.getAllOps():
# 			for m in i.getConnectedOutputs():
# 				for n in m.getConnections():
# 					inOp = self.opFromOpName(n["opName"])
# 					n["attr"] = inOp.getInput(n["attr"])
#
# 			pass
# 		print "rebuilt graph is {}".format(self.opGraph)
# 		return self.opGraph
#
# 	def safeLoadModule(self, mod):
# 		print "loading module {}".format(mod)
# 		module = None
# 		try:
# 			# module = __import__(mod)
# 			module = importlib.import_module(mod)
# 			print "imported module is {}".format(module)
# 			print "imported module class is {}".format(module.__class__)
# 		except Exception as e:
# 			print "ERROR in loading module {}".format(mod)
# 			print "error is {}".format(str(e))
# 		return module
#
# 	@staticmethod
# 	def reconstructOp(info=None, module=None):
# 		# classString = info["MODULE"] + "." + info["CLASS"]
# 		# opInstance = eval(classString)()
# 		# saving this so everyone can see my darkest hour
#
# 		# all necessary modules should have been imported
# 		print ""
# 		print "reconstructOp info is {}".format(info)
# 		print "info MODULE is {}".format(info["MODULE"])
# 		print "info MODULE class is {}".format(info["MODULE"].__class__)
# 		print "info CLASS is {}".format(info["CLASS"])
# 		print "info CLASS class is {}".format(info["CLASS"].__class__)
# 		try:
# 			opClass = getattr(module, info["CLASS"])
# 			opInstance = opClass()
# 		except Exception as e:
# 			print "ERROR in reconstructing op {}".format(info["NAME"])
# 			print "error is {}".format(str(e))
# 			return None
#
# 		print ""
# 		print "reapplying op attributes"
# 		opInstance.opName = info["opName"]
# 		print "default inputs are {}".format(opInstance.inputs)
# 		opInstance.inputRoot = OpAttrItem.fromDict(info["inputRoot"], role="input")
# 		opInstance.outputRoot = OpAttrItem.fromDict(info["outputRoot"], role="output")
#
#
# 		print "new inputs are {}".format(opInstance.inputs)
# 		opInstance.data = info["data"]
#
# 		if "memory" in info.keys():
# 			opInstance.memory.reconstructMemory(info["memory"])
#
# 		return opInstance
#
# 	def renameOp(self, op=None, newName=None):
# 		if self.opFromOpName(newName):
# 			n = 1
# 			print "new op name conflicts with existing op (this is HIGHLY discouraged)"
# 			while self.opFromOpName(newName):
# 				n = n + 1
# 				newName = "{}{}".format(newName, n)
# 				# good enough for maya, good enough for us
#
# 		oldName = op.opName
# 		#### RENAME THE DATAFILE #####
# 		op.renameOp(newName)
# 		if not op.opName in self.opGraph.keys():
# 			print "op {} is not known to the controller, may be unpredictable".format(op.__name__)
# 		else:
# 			self.opGraph[op.opName] = self.opGraph.pop(oldName)
#
#
# 	def opFromOpName(self, opName):
# 		print "looking up opName {}".format(opName)
# 		for k, v in self.opGraph.iteritems():
# 			if k == opName:
# 				return v["op"]
#
#
# 	def opFromOpTrueName(self, opTrueName):
# 		print "looking up opTrueName {}".format(opTrueName)
# 		# get rid of uuid
# 		if len(opTrueName.split("-")) > 2:
# 			opTrueName = opTrueName.split("-")[:-1]
# 		if opTrueName in self.opGraph.keys():
# 			print "found it"
# 			return self.opGraph[opTrueName]
# 		else:
# 			print "na fam"
# 			return False
#
# 	@property
# 	def rigGrp(self):
# 		return core.invokeNode(name=self.character+"_rig", type="transform",
# 		                       func=self.ECA)
#
# 	def ECA(self, type="", name=""):
# 		node = core.ECA(type, name)
# 		Op.addTag(tagNode=node, tagName="character", tagContent=self.character)
#
#
#
# #class LayerOp(Op):
# 	"""base class for sequential operations that make up a rig"""
# 	inputs = {}
# 	data = {}
# 	outputs = {}
# 	extras = {}  # use with caution
# 	GPUable = False
# 	# use to chain surface deformers directly
#
# 	def __init__(self, name=None):
# 		super(LayerOp, self).__init__(name)
# 		self.controller = None
# 		self.redraw = False  # single interface with UI
# 		self.inputRoot = OpAttrItem(role="input", hType="root", name="inputRoot")
# 		self.data = copy.deepcopy(self.data)
# 		self.outputRoot = OpAttrItem(role="output", hType="root", name="outputRoot")
# 		self.defineAttrs() # override this specific method with attr construction
#
# 		self.refreshIo()
#
# 		self.memory = Memory()
# 		self.actions = {}
#
#
#
# 		self.saveData = None
# 		self.dataFileExists = False
# 		print "checking dataFileExists"
# 		self.checkDataFileExists()
#
# 	def ECA(self, type, name="blankName", *args):
# 		node = super(LayerOp, self).ECA(type, name, *args)
# 		if self.controller:
# 			Op.addTag(tagNode=node, tagName="character",
# 			          tagContent=self.controller.character)
# 		return node
#
# 	def defineAttrs(self):
# 		"""override with op specifics"""
# 		raise RuntimeError("op class {} DOES NOT override defineAttrs, please fix".format(
# 			self.__class__.__name__))
#
# 	def refreshIo(self, controller=None, attrChanged=None):
# 		"""interface method with UI or anything else depending on
# 		signals to update attr connections"""
#
# 		pass
#
# 	def log(self, message):
# 		"""if we implement proper logging replace everything here"""
# 		print message
#
# 	@property
# 	def inputs(self):
# 		#return {i.name : i for i in self.inputRoot.getAllChildren()}
# 		return self.inputRoot.getAllChildren()
#
# 	@property
# 	def outputs(self):
# 		#return {i.name : i for i in self.outputRoot.getAllChildren()}
# 		return self.outputRoot.getAllChildren()
#
# 	def callData(self):
# 		return self.data
#
# 	def connectableInputs(self):
# 		self.log("op connectableInputs are {}".format(self.inputRoot.getAllConnectable()))
# 		return self.inputRoot.getAllConnectable()
#
# 	def interactibleInputs(self):
# 		return self.inputRoot.getAllInteractible()
#
# 	def connectableOutputs(self):
# 		return self.outputRoot.getAllConnectable()
#
# 	@staticmethod
# 	def addAttr(parent=None, name=None, dataType=None,
# 	            hType=None, desc="", default=None, attrItem=None,
# 	            *args, **kwargs):
# 		if attrItem:
# 			print "adding attrItem {} directly to {}".format(attrItem.name, parent.name)
# 			return parent.addChild(attrItem)
# 		#print "base addAttr name is {}".format(name)
# 		if parent.attrFromName(name=name):
# 			raise RuntimeError("attr {} already in {} children".format(
# 				name, parent.name))
# 		return parent.addAttr(name=name, dataType=dataType, hType=hType,
# 		                      desc=desc, default=default, *args, **kwargs)
#
# 	def removeAttr(self, name, role="output"):
# 		if role == "output":
# 			attr = self.getOutput(name=name)
# 		else:
# 			attr = self.getInput(name=name)
#
# 		attr.parent.removeAttr(name)
# 		self.redraw = True
# 		self.refreshIo()
#
#
# 	@staticmethod
# 	def addAttrsFromDict(parent=None, fromDict=None):
# 		pass
# 		# for k, v in fromDict.iteritems():
# 		# 	newAttr = None
#
# 	def addInput(self, parent=None, name=None, dataType=None,
# 	             hType="leaf", desc="", default=None, attrItem=None,
# 	             *args, **kwargs):
# 		parent = parent or self.inputRoot
# 		self.redraw = True
# 		return self.addAttr(parent=parent, name=name, dataType=dataType,
# 		                    hType=hType, desc=desc, default=default,
# 		                    attrItem=attrItem, *args, **kwargs)
#
# 	def addOutput(self, parent=None, name=None, dataType=None,
# 	              hType=None, desc="", default=None, attrItem=None,
# 	              *args, **kwargs):
# 		parent = self.outputRoot if not parent else parent
# 		self.redraw = True
# 		return self.addAttr(parent=parent, name=name, dataType=dataType,
# 		                    hType=hType, desc=desc, default=default,
# 		                    attrItem=attrItem, *args, **kwargs)
#
# 	def getInput(self, name):
# 		return self.inputRoot.attrFromName(name)
#
# 	def searchInputs(self, match):
# 		return [i for i in self.inputs if match in i.name]
#
# 	def searchOutputs(self, match):
# 		return [i for i in self.outputs if match in i.name]
#
# 	def getOutput(self, name):
# 		print "getting output {}".format(name)
# 		return self.outputRoot.attrFromName(name)
#
# 	def getConnectedInputs(self):
# 		inputs = self.inputRoot.getAllChildren()
# 		return [i for i in inputs if i.getConnections()]
#
# 	def getConnectedOutputs(self):
# 		outputs = self.outputRoot.getAllChildren()
# 		return [i for i in outputs if i.getConnections()]
#
# 	def clearOutputs(self, search=""):
# 		for i in self.outputs:
# 			if search in i.name or not search:
# 				self.removeAttr(i)
# 		#self.refreshIo()
# 		# do not automatically refresh, let ops call it individually
#
# 	def makeAttrArray(self, archetype=None):
# 		"""intended to be called as part of refreshIo
# 		:param archetype: base attribute to copy from
# 		:archetype is OpAttrItem"""
#
#
#
# 	@property
# 	def dataFilePath(self):
# 		return attrio.dataFolder + self.opName
# 		# one file per op
#
# 	def rename(self, name="newName", renameData=False):
# 		"""interface with abstractGraph"""
# 		super(LayerOp, self).rename(name=name)
# 		self.renameOp(newName=name, renameData=renameData)
#
#
# 	def renameOp(self, newName, renameData=False):
# 		newDataPath = attrio.dataFolder + newName
# 		oldDataPath = self.dataFilePath
# 		self.opName = newName
# 		# check if data exists already
# 		if renameData and not attrio.checkFileExists(newDataPath):
# 			attrio.renameFile(old=oldDataPath, new=newDataPath)
# 		else:
# 			self.checkDataFileExists()
#
#
# 	def checkDataFileExists(self):
# 		if attrio.checkFileExists(self.dataFilePath):
# 			print "data file for {} exists".format(self.opName)
# 			self.dataFileExists = True
# 		else:
# 			print "data file for {} does not exist, making new one".format(self.opName)
# 			attrio.makeBlankFile(path=self.dataFilePath)
# 			self.dataFileExists = True
# 			# not used atm but could be handy
#
# 	def searchData(self, infoName):
# 		return attrio.getData(infoName, self.dataFilePath)
# 		pass
#
# 	def saveOutData(self, infoName="info", data={}):
# 		# golly gee willakers
# 		attrio.updateData(infoName, data, path=self.dataFilePath)
# 		pass
#
# 	def saveOutMemory(self):
# 		attrio.updateData("memory", self.memory.serialiseMemory(),
# 		                  path=self.dataFilePath)
#
# 	def loadMemory(self):
# 		goss = attrio.getData("memory", self.dataFilePath)
# 		self.memory.reconstructMemory(goss)
#
# 	def serialise(self):
# 		orig = super(LayerOp, self).serialise()
# 		orig["memory"] = self.memory.serialiseMemory()
# 		orig["inputRoot"] = self.inputRoot.serialise()
# 		orig["outputRoot"] = self.outputRoot.serialise()
# 		return orig
#
# 	def memoryActions(self):
# 		openDict = self.memory.renewableMemory()
# 		returnDict = {}
# 		for k,v in openDict.iteritems():
# 			returnDict[k] = {}
# 			#for vk, vv in v.iteritems():
# 			returnDict[k][v] = ActionItem({
# 				"func" : self.memory.refresh,
# 				"kwargs" : {
# 					"infoName" : k,
# 					"infoType" : v,
# 				} }, name=v )
# 		return returnDict
#
# 	def remember(self, infoName=None, infoType=None, nodes=None, **kwargs):
# 		"""apply saved data if it exists, create it if not
# 		just a bit of recreational conceptual industrial espionage"""
# 		if infoName in self.memory.infoNames():
# 			if infoType in self.memory.infoTypes(infoName):
# 				self.memory.setNodes(infoName, nodes)
# 				self.memory.recall(infoName, infoType)
# 		self.memory.remember(infoName, infoType, nodes, **kwargs)
#
#
# 	"""EVENTUALLY make this a live link, so every time something is read from
# 	memory object, it's read from the file, and vice versa
# 	or only update files at start and end of build process"""
#
# 	def getAllActions(self):
# 		# returns all right-clickable (or asynchronously callable)
# 		# actions for the op
# 		self.actions.update(self.memoryActions())
# 		print "op getAllActions is {}".format(self.actions  )
# 		return self.actions
#
# 	def addAction(self, actionDict=None, actionItem=None):
# 		if actionDict:
# 			self.actions.update(actionDict)
# 		elif actionItem:
# 			self.actions.update({actionItem.name : actionItem})
#
# 	def addInputWithAction(self, parent=None, name=None, datatype=None, copy=None,
# 	                       suffix="", desc=""):
# 		"""allows user to add input whenever - name or datatype undefined here will
# 		be requested from user as direct input"""
# 		parent = parent or self.inputRoot
# 		def _addInputWithAction(op=self, parent=parent, name=name, datatype=datatype,
# 		                        copy=copy, suffix=suffix, desc=desc):
# 			if not name:
# 				name = raw_input(prompt="name of attribute") + suffix
# 			if not datatype:
# 				datatype = raw_input(prompt="datatype of attribute (in units of D)")
#
# 			op.addInput(parent=parent, name=name, dataType=datatype, desc=desc)
#
# 		actionDict = {
# 			"func" : _addInputWithAction,
# 			"kwargs" : {"op": self}}
# 		inputAction = ActionItem(name="add_custom_input", execDict=actionDict)
# 		self.addAction(actionItem=inputAction)
#
#
#
# 	####### rigOp stages #####
# 	def plan(self):
# 		print "{} running plan stage".format(self.opName)
# 		# CHECK MSTATUS AND RETURN IT
# 		#return 1
# 		# not sure the best way to return the success of an operation
#
# 	def build(self):
# 		print "{} running build stage".format(self.opName)
# 		# CHECK MSTATUS AND RETURN IT
# 		return 1
#
# 	def run(self):
# 		print "{} running run stage".format(self.opName)
# 		# CHECK MSTATUS AND RETURN IT
# 		return 1
#
# 	### auxiliaries ###
#
# 	def onPlanStop(self):
# 		print "{} running onPlanStop".format(self.opName)
# 		pass
#
# 	def onBuildStop(self):
# 		pass
#
# 	def onRunStop(self):
# 		# isn't this just a finished rig?
# 		pass
#
# 	#### maya stuff ####
# 	def invokeNode(self, name="", type="", parent=""):
# 		parent = parent or self.opGrp
# 		return core.invokeNode(name=name, type=type, parent=parent,
# 		                       func=self.ECA)
# 	@property
# 	def rigGrp(self):
# 		return self.controller.rigGrp
#
# 	@property
# 	def opGrp(self):
# 		return self.invokeNode(name=self.opName+"_opGrp", type="transform",
# 		                       parent=self.rigGrp)
# 	@property
# 	def setupGrp(self):
# 		return self.invokeNode(name=self.opName+"_setup", type="transform",
# 		                       parent=self.opGrp)
# 	@property
# 	def controlGrp(self):
# 		return self.invokeNode(name=self.opName+"_controls", type="transform",
# 		                       parent=self.opGrp)