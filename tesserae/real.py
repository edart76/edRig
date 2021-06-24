# real node components to be attached to an abstractNode
# currently for use only in maya, but fully extensible to anything
from __future__ import annotations
from typing import List, Dict, Union, TYPE_CHECKING, Set, Callable



from edRig.lib.python import AbstractTree

from edRig.tesserae.action import Action


from edRig.tesserae.lib import GeneralExecutionManager
# from edRig.lib.deltastack import DeltaStack, StackDelta
# from edRig.tesserae.abstractnode import AbstractAttr
from edRig.tesserae.abstractnode import AbstractNode

import traceback



class AbstractReal(type):
	"""mainly used to facilitate reloading/recasting classes live"""
	def __new__(mcs, *args, **kwargs):
		real = super(AbstractReal, mcs).__new__(*args, **kwargs)
		return real

class RealComponent(AbstractTree):
# class RealComponent(AbstractNode):
	"""base real class to interface with DCCs
	contains memory functionality, attribute lookup and execution
	to be attached to an abstractNode

	for now assume that real components cannot exist without an abstract
	enclosure - no need for checking anywhere

	Q: why not just inherit and save all the hardship
	A: good point
	it's so that abstract nodes can remain ABSTRACT, and the same tesserae
	graph can be loaded (just not fully run) in different environments
	if the real component can't be loaded, its data is still saved and visible
	in the abstract
	"""

	executionManagerType = GeneralExecutionManager

	def __init__(self, name=None, abstract=None, **kwargs):
		super(RealComponent, self).__init__(name=name, **kwargs)
		self._abstract = None
		if abstract:
			self.abstract = abstract
		self.actions = AbstractTree("realActions")


	@property
	def abstract(self)->AbstractNode:
		""":rtype AbstractNode"""
		return self._abstract
	@abstract.setter
	def abstract(self, val:AbstractNode):
		self._abstract = val

	def setAbstract(self, abstract, inDict=None, outDict=None, define=True):
		""" shuffle all required references on to this object
		trying just assigning object methods directly """

		# attributes
		self.addAttr = self.abstract.addAttr
		self.removeAttr = self.abstract.removeAttr
		self.addInput = self.abstract.addInput
		self.addOutput = self.abstract.addOutput
		self.getInput = self.abstract.getInput
		self.getOutput = self.abstract.getOutput

		self.searchInputs = self.abstract.searchInputs
		self.searchOutputs = self.abstract.searchOutputs

		self.connectableInputs = self.abstract.connectableInputs
		self.connectableOutputs = self.abstract.connectableOutputs

		self.interactibleInputs = self.abstract.interactibleInputs

		self.getConnectedInputs = self.abstract.getConnectedInputs
		self.getConnectedOutputs = self.abstract.getConnectedOutputs

		self.clearOutputs = self.abstract.clearOutputs
		self.clearInputs = self.abstract.clearInputs

		# settings
		self.settings = self.abstract.settings
		# self.evaluator = self.abstract.evaluator
		self.addSetting = self.abstract.addSetting

		# sets
		self.addToSet = self.abstract.addToSet
		self.removeFromSet = self.abstract.removeFromSet
		self.getConnectedSets = self.abstract.getConnectedSets

		# signals
		self.sync = self.abstract.sync
		self.attrsChanged = self.abstract.attrsChanged
		self.attrValueChanged = self.abstract.attrValueChanged


	def executionManager(self):
			return self.executionManagerType(self)

	# # attrs to look up on abstract when called from within real
	# deferAttrs = [
	# 	"inputs", "outputs", "inputRoot", "outputRoot",
	# ]
	# directLookups = [
	# 	"abstract", "_abstract"
	# ]
	#
	# # def __getattr__(self, item):
	# # 	if item in RealComponent.directLookups:
	# # 		return object.__getattr__(self, item)
	# #
	# # 	try:
	# # 		return super(RealComponent).__getattr__(self, item)
	# # 	# look up attribute on abstract
	# # 	except:
	# # 		return getattr(self.abstract, item)
	#
	# # dynamic lookups like this can't be run with code completion
	# # feels bad


	# ATTRIBUTES
	@property
	def inputs(self):
		return self.abstract.inputs

	@property
	def outputs(self):
		return self.abstract.outputs

	def addAction(self, action:Union[Callable, function, Action]=None,
	              name=""):
		if isinstance(action, Callable):
			actionItem = Action(action)
		name = name or action.name
		if self.actions.get(name):
			self.actions[name].addAction(action)
		else:
			self.actions[name or action.name] = action

	def getAllActions(self)->AbstractTree[str, Action]:
		return self.actions

# def substituteRoot(self, role="input", newAttr=None):
	# 	"""used to supplant op root attributes with abstract ones"""
	# 	if role == "input":
	# 		attr = self.inputRoot
	# 		vals = attr.serialise()
	# 		self.inputRoot = newAttr.fromDict(vals)
	# 	else:
	# 		attr = self.outputRoot
	# 		vals = attr.serialise()
	# 		self.outputRoot = newAttr.fromDict(vals)

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


class HoudiniReal(RealComponent):
	"""one day"""


