# real node components to be attached to an abstractNode
# currently for use only in maya, but fully extensible to anything

from __future__ import print_function, with_statement

class AbstractReal(type):
	"""mainly used to facilitate reloading/recasting classes live"""
	def __new__(mcs, *args, **kwargs):
		real = super(AbstractReal, mcs).__new__(*args, **kwargs)
		return real

class RealComponent(object):
	"""base real class to interface with DCCs
	contains memory functionality, attribute lookup and execution"""

class MayaReal(RealComponent):
	"""base real class for Maya"""



class HoudiniReal(RealComponent):
	"""one day"""