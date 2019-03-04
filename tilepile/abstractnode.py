# container interfacing with the graph - concerned with connections
from edRig.structures import SafeDict, AttrItem, ActionItem, ActionList
from edRig.core import shortUUID
from edRig import Env, pipeline, attrio
# from edRig.tilepile.ops.op import Op
import functools

class AbstractAbstractNode(type):
	"""abstract class for abstract nodes"""
	def __new__(cls, *args, **kwargs):
		return cls

class AbstractNodeExecutionManager(object):
	"""manages abstract execution, updates ui, etc"""
	def __init__(self, node):
		self.node = node

	def __enter__(self):
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		if exc_type:
			print ""
			print "node {} encountered error during execution".format(self.node.nodeName)
			print "error is {}".format(exc_val)
			#self.node.setState("error")

			# we want execution to stop in this case
			raise exc_type(exc_val)

class AbstractNode(object):
	"""abstract node managed by abstract graph
	interfaces with direct operations, and with UI"""

	# set up action framework
	class action(object):
		"""decorator for asynchronous functions, passed on to real component"""
		actions = {}
		def __init__(self, fn, name=None):
			self.fn = functools.update_wrapper(self, fn)
			self.name = name or fn.__name__
		def __call__(self, *args, **kwargs):
			pass
		# ?????


	defaultName = "basicAbstract"
	realClass = None

	@classmethod
	def nodeType(cls):
		"""for use in managing instantiation"""
		return cls.__name__

	@classmethod
	def setRealClass(cls, realClass):
		cls.realClass = realClass

	def __init__(self, graph, name=None, realInstance=None):
		self.real = None
		self.nodeName = name or self.defaultName + shortUUID(2)

		self.uid = shortUUID(8)
		self.graph = graph
		self.inputRoot = AbstractAttr(node=self, role="input", dataType="null",
		                              hType="root", name="inputRoot")
		self.outputRoot = AbstractAttr(node=self, role="output", dataType="null",
		                              hType="root", name="outputRoot")
		if realInstance:
			real = realInstance
		else:
			real = self.instantiateReal(name=self.nodeName)

		self.extras = None
		self.inEdges = set()
		self.outEdges = set()

		self.index = None # execution order index


		# self.actions = ActionList()
		self.actions = {}
		self.addAction(actionItem=ActionItem(execDict={"func" : self.setApproved},
		                                     name="set approved"))
		self.addAction(actionItem=ActionItem(execDict={"func" : self.recastReal},
		                                     name="recast real"))
		self.dataFileExists = False
		self.setRealInstance(real)
		#self.real.setAbstract(self)


		# ui stuff
		self.pos = [0,0]
		self.colour = self.real.colour
		# self.redraw = False
		# colour-changing nodes could be done if you make this a property
		pass

	@property
	def dataPath(self):
		return self.graph.dataPath + "/" + self.idTag

	@property
	def idTag(self):
		return self.nodeName + "_" + str(self.uid)

	@property
	def edges(self):
		return self.inEdges.union(self.outEdges)

	def instantiateReal(self, name=None):
		return self.realClass(name=name)

	def setRealInstance(self, real, inDict=None, outDict=None, define=True):
		"""sets real component"""
		self.real = real
		self.real.setAbstract(self, inDict=inDict, outDict=outDict, define=define)

	def rename(self, name):
		origPath = self.dataPath
		self.nodeName = name
		#name = self._processName(name)
		# if we ever want to add "-op" to the end of real items or something
		print "RENAMED NODE TO {}".format(name)
		self.real.rename(name) # it's just that easy
		pipeline.renameFile(old=origPath, new=self.dataPath)


	def setApproved(self):
		self.log("this will approve the node")
		pass

	def log(self, message):
		"""if we implement proper logging replace everything here"""
		print message

	# toplogy
	@property
	def history(self):
		return self.graph.getNodesInHistory(self)

	@property
	def future(self):
		return self.graph.getNodesInFuture(self)

	@property
	def fedBy(self):
		return self.graph.getNode(self, entry=True)["fedBy"]

	@property
	def feeding(self):
		return self.graph.getNode(self, entry=True)["feeding"]

	# execution
	def executionStages(self):
		"""returns a list supplied by real component of stages of execution"""
		if not self.real:
			return []
		#funcs = self.real.executionFunctions() # returns safeDict of functions
		#return funcs.keys()
		#self.log("real execStageNames are {}".format(self.real.execStageNames()))
		return self.real.execStageNames()

	def executionFunctions(self):
		"""returns the execution dict of real component"""
		return self.real.execFuncs()

	def getExecFunction(self, index, variant="onExec"):
		"""retrieves specific function"""
		self.log("execIndex is {}".format(index))
		stageName = self.executionStages()[index]
		funcs = self.executionFunctions()[stageName]
		return funcs[variant]

	def execute(self, index, variant="onExec"):
		"""builds a single stage of the real component's execution order
		ATOMIC - CALLED BY EXEC TO STAGE"""
		# do node-level fancy with as error catching here
		func = self.getExecFunction(index, variant)
		return func(self.real)

	def execToStage(self, index):
		"""builds up until a target stage, running stop feature if schedule is incomplete"""
		maxStage = len(self.executionStages())
		if index >= maxStage:
			index = maxStage
		if index == -1: # build everything
			self.execToStage(maxStage-1)
		for i in range(index+1):
			nodeKSuccess = self.execute(i, variant="onExec")
		# check if stage is not end stage
		if index < maxStage -1:
			nodeKSuccess = self.execute(index, variant="onStop")

		self.propagateOutputs()

	def propagateOutputs(self):
		"""references the value of every output to that of every connected input"""
		for i in self.outEdges:
			i.dest[1].value = i.source[1].value




	# ATTRIBUTES
	@property
	def inputs(self):
		#return {i.name : i for i in self.inputRoot.getAllChildren()}
		return self.inputRoot.getAllChildren()

	@property
	def outputs(self):
		#return {i.name : i for i in self.outputRoot.getAllChildren()}
		return self.outputRoot.getAllChildren()

	@staticmethod
	def addAttr(parent=None, name=None, dataType=None,
	            hType=None, desc="", default=None, attrItem=None,
	            *args, **kwargs):
		if attrItem:
			print "adding attrItem {} directly to {}".format(attrItem.name, parent.name)
			return parent.addChild(attrItem)
		#print "base addAttr name is {}".format(name)
		if parent.attrFromName(name=name):
			raise RuntimeError("attr {} already in {} children".format(
				name, parent.name))
		return parent.addAttr(name=name, dataType=dataType, hType=hType,
		                      desc=desc, default=default, *args, **kwargs)

	def removeAttr(self, name, role="output"):
		if role == "output":
			attr = self.getOutput(name=name)
		else:
			attr = self.getInput(name=name)

		attr.parent.removeAttr(name)

	def addInput(self, parent=None, name=None, dataType=None,
	             hType="leaf", desc="", default=None, attrItem=None,
	             *args, **kwargs):
		parent = parent or self.inputRoot
		return self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)

	def addOutput(self, parent=None, name=None, dataType=None,
	              hType="leaf", desc="", default=None, attrItem=None,
	              *args, **kwargs):
		parent = parent or self.outputRoot
		return self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)

	def getInput(self, name):
		return self.inputRoot.attrFromName(name)

	def searchInputs(self, match):
		return [i for i in self.inputs if match in i.name]

	def searchOutputs(self, match):
		return [i for i in self.outputs if match in i.name]

	def getOutput(self, name):
		return self.outputRoot.attrFromName(name)

	def connectableInputs(self):
		#self.log("op connectableInputs are {}".format(self.inputRoot.getAllConnectable()))
		return self.inputRoot.getAllConnectable()

	def interactibleInputs(self):
		return self.inputRoot.getAllInteractible()

	def connectableOutputs(self):
		return self.outputRoot.getAllConnectable()

	def getConnectedInputs(self):
		inputs = self.inputRoot.getAllChildren()
		return [i for i in inputs if i.getConnections()]

	def getConnectedOutputs(self):
		outputs = self.outputRoot.getAllChildren()
		return [i for i in outputs if i.getConnections()]

	def clearOutputs(self, search=""):
		for i in self.outputs:
			if search in i.name or not search:
				self.removeAttr(i)


	# actions and real-facing methods
	def getAllActions(self):
		#self.addAction(self.getRealActions())
		actions = {}
		actions.update(self.actions)
		actions.update(self.getRealActions())
		return actions
		#return self.actions

	def getRealActions(self):
		return self.real.getAllActions() # dict

	def addAction(self, actionDict=None, actionItem=None):
		if actionDict:
			self.actions.update(actionDict)
		elif actionItem:
			self.actions.update({actionItem.name : actionItem})

	def getExecActions(self):
		"""this is kind of a mess - allows executing specific nodes to specific
		stages"""
		actions = {}
		for i, val in enumerate(self.executionStages()):
			actionDict = {"func" : self.execToStage, "args" : [i]}
			actions.update({val : ActionItem(name=val, execDict=actionDict)})
		return actions

	def recastReal(self):
		"""for use in developing real components live - replaces class of real component
		with current version"""
		newReal = self.real.fromDict(self.real.serialise())
		self.setRealInstance(newReal)

	# graph io
	def checkDataFileExists(self):
		if attrio.checkFileExists(self.dataPath):
			print "data file for {} exists".format(self.nodeName)
			self.dataFileExists = True
		else:
			print "data file for {} does not exist, making new one".format(self.nodeName)
			attrio.makeBlankFile(path=self.dataPath)
			self.dataFileExists = True

	def searchData(self, infoName):
		print "abstract getting data" + infoName
		self.checkDataFileExists()
		return attrio.getData(infoName, self.dataPath)
		pass

	def saveOutData(self, infoName="info", data={}):
		# golly gee willakers
		print "abstract saving data " + infoName
		self.checkDataFileExists()
		attrio.updateData(infoName, data, path=self.dataPath)


	def serialise(self):
		"""converts node and everything it contains to dict"""
		serial = {
			"uid" : self.uid,
			"nodeName" : self.nodeName,
			"inputRoot" : self.inputRoot.serialise(),
			"outputRoot" : self.outputRoot.serialise(),
			"extras" : self.extras,
			#"CLASS" : self.__class__.__name__
		}
		if self.real:
			serial["real"] = self.real.serialise()
		return serial

	@classmethod
	def fromDict(cls, fromDict, graph=None):
		"""classmethod because returned abstract should be the right child class
		so this is carnage"""
		realClass = None
		# try to load real component class from module

		if "real" in fromDict.keys():
			realDict = fromDict["real"]
			module = realDict["MODULE"]
			loadedModule = pipeline.safeLoadModule(module)
			try:
				realClass = getattr(loadedModule, realDict["CLASS"])
			except Exception as e:
				print "ERROR in reconstructing op {}".format(realDict["NAME"])
				raise e

		if realClass:
			newClass = cls.generateAbstractClass(realClass)
		else:
			newClass = cls

		# abstract reconstruction
		newInst = newClass(graph)
		newInst.uid = fromDict["uid"]
		newInst.rename(fromDict["nodeName"])

		newInst.outputRoot = AbstractAttr.fromDict(fromDict=fromDict["outputRoot"],
		                                           node=newInst)
		newInst.inputRoot = AbstractAttr.fromDict(fromDict=fromDict["inputRoot"],
		                                          node=newInst)
		print ""
		print "ABSTRACT FROMDICT KEYS ARE {}".format(fromDict.keys())


		if "real" in fromDict.keys():
			realDict = fromDict["real"]
			realInstance = realClass.fromDict(realDict, abstract=newInst)
			print "realInstance is {}".format(realInstance)
			# we sort of do this twice but for now it works
			# newInst.setRealInstance(realInstance,
			#                         inDict=fromDict["real"]["inputRoot"],
			#                         outDict=fromDict["real"]["outputRoot"])
			# # attributes are the goddamn thing
			# """setRealInstance has to call defineAttrs - we need to reapply the right
			# attributes afterwards"""
			newInst.setRealInstance(realInstance, define=False)
		return newInst

	@staticmethod
	def generateAbstractClass(realClass):
		realClassName = realClass.__name__
		abstractClass = type(realClassName, (AbstractNode,),
		                     {"realClass": realClass})
		return abstractClass

	def delete(self):
		"""deletes abstract node and real component
		edges will already have been deleted by graph"""
		self.inputRoot.delete()
		self.outputRoot.delete()
		self.real.delete()


class AbstractAttr(AttrItem):
	"""simple object marking separate inputs and outputs to AbstractNodes
	also incorporating hierarchy"""

	accepts = { # key accepts connections of type value
		"nD" : ["0D", "1D", "2D", "3D"],
		# this should probably be exposed to user per-attribute
	}
	# def __init__(self, *args, **kwargs):
	# 	"""adds reference to an abstractNode, because it's just easier"""
	# 	super(AbstractAttr, self).__init__(*args, **kwargs)
	# 	# that feel when you monkeypatch your own objects for readibility

	def addConnection(self, edge):
		"""ensures that input attributes will only ever have one incoming
		connection"""
		if edge in self.connections:
			Env.log("skipping duplicate edge on attr {}".format(self.name))
			return
		if self.role == "output":
			self.connections.append(edge)
		else:
			self.connections = [edge]

	def addChild(self, newChild):
		newChild = super(AbstractAttr, self).addChild(newChild)
		newChild.node = self.node

	@property
	def abstract(self):
		return self.node




