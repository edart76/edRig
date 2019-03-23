# real node components to be attached to an abstractNode
# currently for use only in maya, but fully extensible to anything

from __future__ import print_function, with_statement
from edRig.tilepile.lib import DeltaStack, StackDelta

class GeneralExecutionManager(object):
	"""placeholder"""
	def __init__(self, real):
		self.real = real

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

class MayaReal(RealComponent):
	"""base real class for Maya"""

class MayaStack(DeltaStack):
	"""maya-specialised stack for tracking deltas in scenes"""

class MayaDelta(StackDelta):
	"""atomic maya scene delta, tracking addition, removal or
	modification of nodes"""


class HoudiniReal(RealComponent):
	"""one day"""

