"""support for evaluating string expressions, mainly from settings"""

from edRig.lib.python import AbstractTree
# from edRig import DCC_ENVIRONMENT

"""need to evaluate entries in an AbstractTree, and raise a signal error
if it fails, including proper path to entry
evaluation and conditions for success will only be known in real context - 
there could be support for doing pure abstract lookups in a purely abstract setting,
but for now not necessary"""

class AbstractEvaluator(object):
	"""base class for abstract-level expression execution"""
	def __init__(self, graph, node=None):
		self.graph = graph # expressions at least need graph to evaluate
		self.node = node # node is nifty, but not required

class MayaEvaluator(AbstractEvaluator):
	"""maya-specific evaluator, allowing maya attribute lookups
	and node calculator"""


# change based on program environment
EVALUATOR = MayaEvaluator