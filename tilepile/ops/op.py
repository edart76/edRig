# base op
from maya import cmds
import maya.api.OpenMaya as om
from edRig.core import ECA, ECN, AbsoluteNode, shortUUID, invokeNode
from edRig import Env, attrio, scene, attr
from edRig.tilepile.abstractnode import AbstractAttr
import random, copy, functools
from edRig.structures import ActionItem
from edRig.pipeline import safeLoadModule

from edRig.tilepile.real import MayaReal

class OpExecutionManager(object):
	def __init__(self, op):
		self.op = op
		self.beforeSet = None
		self.afterSet = None

	def __enter__(self):
		self.beforeSet = scene.listTopNodes()
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
		"""clean up maya scene nodes regardless"""
		self.afterSet = scene.listTopNodes()
		new = self.afterSet - self.beforeSet
		cmds.parent(new, self.op.setupGrp)

		# halt execution
		if exc_type:
			raise exc_type(exc_val)



class Op(MayaReal):
	# base class for "operations" executed by abstractGraph,
	# mainly maya scripting
	opName = None
	colour = (100, 100, 150) # rgb

	# set up action framework

	# execution architecture
	@classmethod
	def execStageNames(cls):
		"""returns names of stages IN ORDER"""
		#execStages = ["plan", "build"]
		execStages = ["execute"]
		return execStages

	@classmethod
	def execFuncs(cls):
		"""all execution stages associated with class"""
		# return {
		# 	"plan" : {"onExec" : cls.plan,
		# 	          "onStop" : cls.onPlanStop},
		# 	"build" : {"onExec" : cls.build,
		# 	           "onStop" : cls.onBuildStop},}
		return {"run" : cls.execute}

	@classmethod
	def classRigGrp(cls):
		"""base group for all tilePile stuff, named by character eventually"""
		return invokeNode(name="tilePile", type="transform")

	dataMapping = {
		"0D" : "matrix",
		"1D" : "nurbsCurve",
		"2D" : "mesh",
		"string" : "string",
	}

	def __init__(self, name=None, abstract=None):
		self.character = None
		print "Op instantiated"
		self._opName = None
		if not name:
			self.opName = self.__class__.__name__
		else:
			self.opName = name

		self.uuid = self.shortUUID(4)
		if abstract:
			self.inputRoot = abstract.inputRoot
			self.outputRoot = abstract.outputRoot
		else:
			print "no abstract passed"
			self.inputRoot = AbstractAttr(role="input", hType="root", name="inputRoot")
			self.outputRoot = AbstractAttr(role="output", hType="root", name="outputRoot")
		self.defineAttrs() # override this specific method with attr construction
		self.data = copy.deepcopy(self.data)
		self.redraw = False  # single interface with UI
		self.abstract = None
		if abstract:
			self.setAbstract(abstract)
		#self.refreshIo()
		self.actions = {}
		self.addAction(actionItem=ActionItem(name="clear Maya scene", execDict=
			{"func" : self.clearMayaRig}))

		# network nodes holding input and output plugs
		self.inputNetwork = None
		self.outputNetwork = None

	def beforeExecution(self):
		"""create network nodes procedurally from attributes"""
		self.inputNetwork = self.ECA("network", name=self.opName+"_inputs")
		self.outputNetwork = self.ECA("network", name=self.opName + "_outputs")

		attr.makeStringConnection(self.inputNetwork, self.outputNetwork,
								  startName="opStart", endName="opEnd")

		for i in self.inputRoot.getAllLeaves():
			self.makeOpIoNodes(self.inputNetwork, i)

		for i in self.outputRoot.getAllLeaves():
			self.makeOpIoNodes(self.outputNetwork, i)

	def makeOpIoNodes(self, node, attr):
		""":param node: AbsoluteNode
		:param attr : AbstractAttr"""
		#for i in attr.getAllChildren(): # get all leaves maybe?
		# convert datatype to pass to addattr
		if i.dataType in self.dataMapping.keys():
			dt = self.dataMapping[i.dataType]

			cmds.addAttr(node, ln=attr.name, dt=dt)
		elif i.dataType == "enum":
			options = ":".join(i.extras.get("items"))
			cmds.addAttr(node, ln=attr.name, at="enum",
						 enumName=options)
		else:
			dt = i.dataType
			cmds.addAttr(node, ln=attr.name, at=dt)
		i.plug = node+"."+i.name
		return i.plug


	def setAbstract(self, abstract, inDict=None, outDict=None, define=True):
		"""attach op to abstractNode, and merge input and outputRoots"""
		self.abstract = abstract
		self.inputRoot = abstract.inputRoot
		self.outputRoot = abstract.outputRoot
		if define:
			self.defineAttrs()
		#print "outputs after defineAttrs are {}".format(self.outputs)
		# support for redefining attributes from dict
		if inDict:
			self.inputRoot = self.inputRoot.fromDict(inDict, node=abstract)
		if outDict:
			self.outputRoot = self.outputRoot.fromDict(outDict, node=abstract)
		# no luck all skill
		self.redraw=True
		#print "outputs after setAbstract are {}".format(self.outputs)

		# i would really like some meta way to supplant all op-level methods
		# with the "correct" abstract-level versions

	@property
	def __name__(self):
		# return str(self.__class__) + "-" + self.opName + "-" + self.uuid
		return str(self.__class__.__name__) + "-" + self.opName

	def rename(self, newName):
		"""called by graph"""
		self.opName = newName

	@property
	def opName(self):
		# because this wasn't confusing enough already
		if self._opName:
			return self._opName
		else:
			return self.__class__.__name__ #+ self.uuid

	@opName.setter
	def opName(self, val):
		# equivalent to renaming an op
		self._opName = val
		# return val

	@staticmethod
	def log(message, **kwargs):
		"""if we implement proper logging replace everything here"""
		Env.log(message, **kwargs)

	@property
	def inputs(self):
		#return {i.name : i for i in self.inputRoot.getAllChildren()}
		if self.abstract:
			return self.abstract.inputRoot.getAllChildren()
		return self.inputRoot.getAllChildren()

	@property
	def outputs(self):
		#return {i.name : i for i in self.outputRoot.getAllChildren()}
		if self.abstract:
			return self.abstract.outputRoot.getAllChildren()
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
			print "attr {} already in {} children".format(
				name, parent.name)
			return parent.attrFromName(name)
		return parent.addAttr(name=name, dataType=dataType, hType=hType,
		                      desc=desc, default=default, *args, **kwargs)

	def removeAttr(self, name, role="output"):
		if role == "output":
			attr = self.getOutput(name=name)
		else:
			attr = self.getInput(name=name)

		attr.parent.removeAttr(name)
		self.redraw = True
		self.refreshIo()


	@staticmethod
	def addAttrsFromDict(parent=None, fromDict=None):
		pass
		# for k, v in fromDict.iteritems():
		# 	newAttr = None

	def addInput(self, parent=None, name=None, dataType=None,
	             hType="leaf", desc="", default=None, attrItem=None,
	             *args, **kwargs):
		parent = parent or self.inputRoot
		self.redraw = True
		return self.addAttr(parent=parent, name=name, dataType=dataType,
		                    hType=hType, desc=desc, default=default,
		                    attrItem=attrItem, *args, **kwargs)

	def addOutput(self, parent=None, name=None, dataType=None,
	              hType="leaf", desc="", default=None, attrItem=None,
	              *args, **kwargs):
		parent = self.outputRoot if not parent else parent
		self.redraw = True
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
		# print "getting output {}".format(name)
		# print "current outputs are {}".format(self.outputs)
		return self.outputRoot.attrFromName(name)

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
		#self.refreshIo()
		# do not automatically refresh, let ops call it individually

	def makeAttrArray(self, archetype=None):
		"""intended to be called as part of refreshIo
		:param archetype: base attribute to copy from
		:archetype is OpAttrItem"""

	def defineAttrs(self):
		"""override with op specifics"""
		raise NotImplementedError("op class {} DOES NOT override defineAttrs, please fix".format(
			self.__class__.__name__))

	def refreshIo(self, controller=None, attrChanged=None):
		"""interface method with UI or anything else depending on
		signals to update attr connections"""
		pass

	def connectableInputs(self):
		self.log("op connectableInputs are {}".format(self.inputRoot.getAllConnectable()))
		return self.inputRoot.getAllConnectable()

	def interactibleInputs(self):
		return self.inputRoot.getAllInteractible()

	def connectableOutputs(self):
		return self.outputRoot.getAllConnectable()

	def substituteRoot(self, role="input", newAttr=None):
		"""used to supplant op root attributes with abstract ones"""
		if role == "input":
			attr = self.inputRoot
			vals = attr.serialise()
			self.inputRoot = newAttr.fromDict(vals)
		else:
			attr = self.outputRoot
			vals = attr.serialise()
			self.outputRoot = newAttr.fromDict(vals)

	# ever look at a node and think
	# wtf are you
	@staticmethod
	def edTag(tagNode):
		# more tactile to have a little top tag
		cmds.addAttr(tagNode, ln="edTag", dt="string", writable=True)
		happyList = [
			":)", ":D", ".o/", "^-^", "i wish you happiness",
			"bein alive is heckin swell!!!", "it's a beautiful day today",
		]
		ey = random.randint(0, len(happyList) - 1)
		cmds.setAttr(tagNode + ".edTag", happyList[ey], type="string")
		cmds.setAttr(tagNode + ".edTag", l=True)

	@staticmethod
	def checkTag(tagNode, op=None, specific=False):
		# checks if a node has a specific edTag
		testList = cmds.listAttr(tagNode, string="edTag")

		if testList:
			return True
		else:
			return False

	@staticmethod
	def addTag(tagNode, tagName, tagContent=None):
		# use string arrays(?) to store op that created tag as well as type
		# better to store content of string as dictionary
		if Op.checkTag(tagNode) == False:
			Op.edTag(tagNode)

		cmds.addAttr(tagNode, ln=tagName, dt="string")
		if tagContent:
			# tag content can be anything, keep track of it yourself
			cmds.setAttr(tagNode + "." + tagName, tagContent, type="string")

	@staticmethod
	def getTag(tagNode, tagName=None):
		# retrieves specific tag information, or lists all of it
		if tagName:
			gotTag = cmds.getAttr(tagNode + "." + tagName)
		else:
			gotTag = cmds.listAttr(tagNode, string="*tag")
		return gotTag

	# might be useful

	def opTag(self, tagNode):
		# add tag for the specific op
		if self.opName:
			cmds.addAttr(tagNode, ln="opTag", dt="string", writable=True)
			cmds.setAttr(tagNode + ".opTag", self.opName, type="string")

	def ECN(self, type, name="blankName", cleanup=True, *args):
		# this is such a good idea
		if name == "blankName":
			name = type
		node = ECN(type, name, *args)
		self.edTag(node)
		self.opTag(node)
		# print "node is {}".format(node)
		# print "self.opGrp is {}".format(self.opGrp)
		if cleanup:
			node = cmds.parent(node, self.opGrp)[0] # prevent messy scenes
		return node

	def ECAsimple(self, type, name="blankName", cleanup=False, *args):
		# this is such a good idea
		# first check if node already exists, later
		node = self.ECN(type, *args, name=name, cleanup=cleanup)
		return AbsoluteNode(node)

	def ECA(self, type, name="blankName", *args):
		node = self.ECAsimple(type, name, cleanup=True, *args)
		#cmds.parent(node, self.opGrp)
		return node

	@staticmethod
	def shortUUID(length=4):
		return shortUUID(length=length)

	# execution methods - override at will
	# def plan(self):
	# 	pass
	#
	# def build(self):
	# 	pass
	#
	# def onPlanStop(self):
	# 	print "{} running onPlanStop".format(self.opName)
	# 	pass
	#
	# def onBuildStop(self):
	# 	pass
	#
	# def onRunStop(self):
	# 	# isn't this just a finished rig?
	# 	pass

	def execute(self):
		raise NotImplementedError()


	def showGuides(self):
		"""used to allow user direction over op, as a separate process
		to execution"""
		pass

	# io
	def searchData(self, infoName):
		return attrio.getData(infoName, self.dataFilePath)
		pass

	def saveOutData(self, infoName="info", data={}):
		# golly gee willakers
		print "op saving data"
		self.checkDataFileExists()
		attrio.updateData(infoName, data, path=self.dataFilePath)


	# actions
	def getAllActions(self):
		return self.actions

	def addAction(self, actionDict=None, actionItem=None):
		if actionDict:
			self.actions.update(actionDict)
		elif actionItem:
			print "adding action {}".format(actionItem)
			self.actions.update({actionItem.name : actionItem})

	def addInputWithAction(self, parent=None, name=None, datatype=None, copy=None,
	                       suffix="", desc=""):
		"""allows user to add input whenever - name or datatype undefined here will
		be requested from user as direct input"""
		parent = parent or self.inputRoot
		def _addInputWithAction(op=self, parent=parent, name=name, datatype=datatype,
		                        copy=copy, suffix=suffix, desc=desc):
			if not name:
				name = raw_input(prompt="name of attribute") + suffix
			if not datatype:
				datatype = raw_input(prompt="datatype of attribute (in units of D)")

			op.addInput(parent=parent, name=name, dataType=datatype, desc=desc)

		actionDict = {
			"func" : _addInputWithAction,
			"kwargs" : {"op": self}}
		inputAction = ActionItem(name="add_custom_input", execDict=actionDict)
		self.addAction(actionItem=inputAction)


	# def action(self, name=None):
	# 	def decoOuter(func):
	# 		@functools.wraps(func)
	# 		def decoInner(*args, **kwargs):
	# 			return func(*args, **kwargs)
	# 		print ""
	# 		print "adding action from deco"
	# 		# self.addAction(actionItem=ActionItem(name=name or func.__name__,
	# 		#                                      execDict={"func": func,
	# 		#                                                "args": args,
	# 		#                                                "kwargs": kwargs}))
	# 		self.addAction(actionItem=ActionItem(name=name or func.__name__,
	# 		                                     execDict={"func": func}))
	# 		return decoInner
	# 	return decoOuter


	# serialisation and regeneration
	def serialise(self):
		opDict = {}
		opDict["NAME"] = self.__name__
		opDict["CLASS"] = self.__class__.__name__
		opDict["MODULE"] = self.__class__.__module__
		opDict["opName"] = self.opName
		copyData = copy.copy(self.data)
		opDict["data"] = copyData
		opDict["inputRoot"] = self.inputRoot.serialise()
		opDict["outputRoot"] = self.outputRoot.serialise()
		return opDict

	@staticmethod
	def fromDict(regenDict, abstract=None):
		"""regenerates op from dict"""
		module = regenDict["MODULE"]
		loadedModule = Op.safeLoadModule(module)
		try:
			opClass = getattr(loadedModule, regenDict["CLASS"])
			opInstance = opClass()
		except Exception as e:
			print "ERROR in reconstructing op {}".format(regenDict["NAME"])
			print "error is {}".format(str(e))
			return None

		opInstance.opName = regenDict["opName"]
		# print "default inputs are {}".format(opInstance.inputs)
		if abstract:
			opInstance.inputRoot = abstract.inputRoot
			opInstance.outputRoot = abstract.outputRoot
		else:
			opInstance.inputRoot = AbstractAttr.fromDict(regenDict["inputRoot"])
			opInstance.outputRoot = AbstractAttr.fromDict(regenDict["outputRoot"])


		# print "new inputs are {}".format(opInstance.inputs)
		# print "new outputs are {}".format(opInstance.outputs)
		opInstance.data = regenDict["data"]
		return opInstance

	@staticmethod
	def safeLoadModule(mod):
		"""takes string name of module"""
		return safeLoadModule(mod)

	def delete(self):
		"""deletes op instance"""
		del self



	#### maya stuff ####
	# yes i know this should go in a DCC-specific child class, but there's
	# absolutely no point right now
	def invokeNode(self, name="", type="", parent="", func=None):
		parent = parent or self.opGrp
		func = func or self.ECA
		return invokeNode(name=name, type=type, parent=parent,
		                       func=func)

	def clearMayaRig(self):
		"""clears all edRig items from maya scene - this method needs a home"""
		cmds.file(new=True, f=True)

	@property
	def rigGrp(self):
		return self.classRigGrp()

	@property
	def opGrp(self):
		return self.invokeNode(name=self.opName+"_opGrp", type="transform",
		                       parent=self.rigGrp, func=self.ECAsimple)
	@property
	def setupGrp(self):
		return self.invokeNode(name=self.opName+"_setup", type="transform",
		                       parent=self.opGrp, func=self.ECAsimple)
	@property
	def controlGrp(self):
		return self.invokeNode(name=self.opName+"_controls", type="transform",
		                       parent=self.opGrp, func=self.ECAsimple)