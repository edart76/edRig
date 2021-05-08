"""support for evaluating string expressions, mainly from settings"""


import string, re, ast, math, uuid

from edRig.lib.python import AbstractTree, Signal


"""need to evaluate entries in an AbstractTree, and raise a signal error
if it fails, including proper path to entry
evaluation and conditions for success will only be known in real context - 
there could be support for doing pure abstract lookups in a purely abstract setting,
but for now not necessary

variables are accessed via $var syntax, just for consistency
no that's disgusting
via (var) syntax

been a little while: a more realistic use case has appeared
consider a situation like hierarchy building - 

L_forearm_grp : [L_ulna, L_radius, L_semilunateCarpal, L_carpalA, etc...]
that has to be copied, every occurrence of L changed to R
if anything changes, needs to be redone
WE CAN DO BETTER

<L, R>_forearm_grp : [<L,R>_ulna, <L,R>_radius, <L,R>_semilunateCarpal]

I think this is a good start, we still duplicate typing <L,R> template though
Expression will scan through for these template tokens, then iterate through strings

' what if we want distinct iteration of every separate token ' glad you asked
<L,R> links to <L,R>
<L,R> does not link to <L,R>> or <<L,R>
bit crude but this usecase is kind of crude anyway
ignoring this until it matters, this can't be the best way
brackets always guaranteed to be balanced

if we introduce hysteresis and state we can do
[<L,R>_ulna, <>_radius, <>_semilunateCarpal]
but this is more complex, more fragile, more confusing, not worth it

found a better way to approach this particular usecase
more verbose and more readable

"""


bracketExp = re.compile("<(.*?)>")

def runTemplatedStrings(stringList):
	""" consider several strings as one in template operation """
	data, breakSeq = joinStringsBreakpoint(stringList)
	formatted = templateString(data)
	# split strings after processing
	fsplit = [i.split(breakSeq) for i in formatted]
	return fsplit

def templateString(data):
	""" return permutations of string for every template token it contains """
	tokenSet = set(bracketExp.findall(data))
	if not tokenSet:
		return [data]
	combos = tokenPermutations(list(tokenSet))  # list of dicts
	formatted = []
	for combo in combos:
		parsed = data
		for token, value in combo.items():
			parsed = parsed.replace(
				"<{}>".format(token), value)
		formatted.append(parsed)
	return formatted


def tokenPermutations(tokens, _valueDict=None, _resultList=None):
	"""valueDict = dict of token : value throughout permutation
	this was my first stab at recursive permutation, please have mercy
	after the fact looks like this is called backtracking """
	_valueDict = _valueDict or {}
	_resultList = _resultList or []
	values = tokens[0].split(",")
	for i in range(len(values)):
		_valueDict[tokens[0]] = values[i]
		if len(tokens) > 1:
			_resultList = tokenPermutations( tokens[1:], _valueDict, _resultList )
		else: # bottom of permutation
			_resultList.append(dict(_valueDict))
	return _resultList


def joinStringsBreakpoint(stringList):
	""" joins strings with a unique breakpoint sequence,
	to combine for easier processing and then split """
	breakSeq = str(hash(
		"tjwasaninsidejob".join(stringList) ))
	return breakSeq.join(stringList), breakSeq




if __name__ == '__main__':

	testList = ["<L,R>_arm_grp", "<A,B>_ulna, <L,R>_radius, <L,R>_carpal"]
	result = runTemplatedStrings(testList) # works
	print(result)

	testString = "L_arm_grp"
	print(templateString(testString))

	testList = ["L_arm_grp", "R_carpal"]
	result = runTemplatedStrings(testList) # works
	print(result)


	testString = "<L,R>_ulna, <L,R>_radius, <L,R>_carpal"
	result = re.findall("<(.*?)>", testString) # ['L,R', 'L,R', 'L,R']

	testString = "<L,R>_ulna, <A,B>_radius, <L,R>_carpal"
	result = re.findall("<(.*?)>", testString)  # ['L,R', 'A,B', 'L,R']

	testString = "<L,R>_ulna, <A,B>_radius, <L,R>_carpal"
	result = re.match("<(.*?)>", testString)
	result = result.groups() # ('L,R',) hmmm


class Token(object):
	pass

delimiters = "<>"
def collectTokens(span):
	""" runs over input span and collects balanced, nested tokens """
	for i in range(span):
		if i == delimiters[0]:
			pass #?


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

# class MayaEvaluator(AbstractEvaluator):
# 	"""maya-specific evaluator, allowing maya attribute lookups
# 	and node calculator"""
#
# 	@classmethod
# 	def applyExpressionOutput(cls, target, result):
# 		"""in maya, connects plug if it is a plug, sets it if not"""
# 		attr.conOrSet(result, target)
#
# 	def evaluateExpression(self, endTarget, expression):
# 		"""knowing the end target (ie the output plug),
# 		evaluate expression to find what to do with it
# 		master function """
#
# 		try: # what are context handlers
# 			# parse the expression, if possible convert to nodeCalculator compatible form
# 			## etc
#
# 			# only set if it's a flat value - if expression contains any maya plugs,
# 			# assume it's all live
#
# 			result = "" # output plug or result to
# 			success = self.applyExpressionOutput(endTarget, result)
# 			return success
# 		except:
# 			return False
#
# 	def evaluateSettings(self, test):
# 		"""placeholder
# 		op should technically parse tree to find end target, then pass that to evaluator"""
# 		return True


# change based on program environment
#EVALUATOR = MayaEvaluator
