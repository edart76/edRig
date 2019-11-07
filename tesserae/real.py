# real node components to be attached to an abstractNode
# currently for use only in maya, but fully extensible to anything

from __future__ import print_function, with_statement
from edRig.tesserae.lib import GeneralExecutionManager
from edRig.lib.deltastack import DeltaStack, StackDelta
from edRig.tesserae.abstractnode import AbstractAttr
import traceback



class AbstractReal(type):
	"""mainly used to facilitate reloading/recasting classes live"""
	def __new__(mcs, *args, **kwargs):
		real = super(AbstractReal, mcs).__new__(*args, **kwargs)
		return real

class RealComponent(object):
	"""base real class to interface with DCCs
	contains memory functionality, attribute lookup and execution
	to be attached to an abstractNode"""

	def executionManager(self):
		return GeneralExecutionManager(self)


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
			result = parent.addChild(attrItem)

		if parent.attrFromName(name=name):
			result = parent.attrFromName(name)
		else: result = parent.addAttr(name=name, dataType=dataType, hType=hType,
		                      desc=desc, default=default, *args, **kwargs)
		return result

	def removeAttr(self, name, role="output"):
		if role == "output":
			attr = self.getOutput(name=name)
		else:
			attr = self.getInput(name=name)

		attr.parent.removeAttr(name)
		self.redraw = True
		self.sync()


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
		""":returns AbstractAttr"""
		return self.inputRoot.attrFromName(name)

	def searchInputs(self, match):
		return [i for i in self.inputs if match in i.name]

	def searchOutputs(self, match):
		return [i for i in self.outputs if match in i.name]

	def getOutput(self, name):
		"""
		:param name:
		:return: AbstractAttr
		"""
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
		:archetype is """

	def refreshIo(self):
		"""leftover garbage, now used just to call sync"""
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

class RealAttrInterface(object):
	"""this can be assigned to an attribute procedurally by real class
	designed to return the actual real component of the attribute through repr"""


	def __init__(self, attrItem, mainReal):
		self.attrItem = attrItem
		self.mainReal = mainReal

	def __call__(self, *args, **kwargs):
		return self.getRealAttrComponent()

	def __str__(self):
		return self.getRealAttrComponent()

	def getRealAttrComponent(self):
		"""override this specifically for dcc"""
		raise NotImplementedError()

class MayaReal(RealComponent):
	"""base real class for Maya"""

# class MayaStack(DeltaStack):
class MayaStack(object):
	"""maya-specialised stack for tracking deltas in scenes"""

class MayaDelta(StackDelta):
	"""atomic maya scene delta, tracking addition, removal or
	modification of nodes"""


class HoudiniReal(RealComponent):
	"""one day"""


