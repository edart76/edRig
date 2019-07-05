"""support for evaluating string expressions, mainly from settings"""

from edRig.lib.python import AbstractTree, Signal
from edRig import attr
from node_calculator import core as noca # big oofs in chat
# from edRig import DCC_ENVIRONMENT

"""need to evaluate entries in an AbstractTree, and raise a signal error
if it fails, including proper path to entry
evaluation and conditions for success will only be known in real context - 
there could be support for doing pure abstract lookups in a purely abstract setting,
but for now not necessary

variables are accessed via $var syntax, just for consistency
no that's disgusting
via (var) syntax"""

class AbstractEvaluator(object):
	"""base class for abstract-level expression execution"""


	def __init__(self, graph, node=None):
		""":param graph : AbstractGraph"""
		self.graph = graph # expressions at least need graph to evaluate
		self.node = node # node is nifty, but not required

		self.globalVars = {
			"asset" : self.graph.asset,
			"name" : self.node.nodeName,
		}

	def getGlobalVar(self, varString):
		"""expects variable with $sign attached"""
		var = varString[1:]
		return self.globalVars[var]

	@staticmethod
	def stripWhitespace(string=""):
		"""first just strip whitespace?"""
		newString = "".join(string.split())
		return newString

class MayaEvaluator(AbstractEvaluator):
	"""maya-specific evaluator, allowing maya attribute lookups
	and node calculator"""

	@classmethod
	def applyExpressionOutput(cls, target, result):
		"""in maya, connects plug if it is a plug, sets it if not"""
		attr.conOrSet(result, target)

	def evaluateExpression(self, endTarget, expression):
		"""knowing the end target (ie the output plug),
		evaluate expression to find what to do with it
		master function """

		try: # what are context handlers
			# parse the expression, if possible convert to nodeCalculator compatible form
			## etc

			# only set if it's a flat value - if expression contains any maya plugs,
			# assume it's all live

			result = "" # output plug or result to
			success = self.applyExpressionOutput(endTarget, result)
			return success
		except:
			return False

	def evaluateSettings(self, test):
		"""placeholder
		op should technically parse tree to find end target, then pass that to evaluator"""
		return True


# change based on program environment
EVALUATOR = MayaEvaluator




"""there isn't really a better way than node calculator to set up simple expressions driving nodes;
it does mean some serious string processing to get some usable python out of it before
we evaluate it with noca"""
