
import sys, os, fnmatch, json
from pprint import pprint, pformat
import inspect, functools, itertools
import keyword

from typing import List, Type, Tuple, Set, AnyStr, Dict

from maya import cmds

#import maya_signatures

outputPath = "F:/all_projects_desktop/common/edCode/edRig/tool/stubgen/result/cmds.pyi"

# cmds seems to have <class 'function'> for wrapped MEL scripts, and
# <class 'builtin_function_or_method'> for actual cmds calls
# good to know


def formatFunction (fnName,
                    flagSeq:List):
	"""return the formatted header for a function"""
	#print(flagSeq)
	argTokens = []
	for name, valSequence in flagSeq:
		if keyword.iskeyword(name):
			continue
		if len(valSequence) == 1:
			argTokens.append("{}:{}=None".format(
				name, valSequence[0].__name__
			))
		else: # tuple of types
			tupleStr = "Tuple[{}]".format(", ".join(
				i.__name__ for i in valSequence))
			argTokens.append("{}:{}=None".format(
				name, tupleStr))

	argFieldString = ", ".join(argTokens)

	rTypeString = "->List" or ""

	docString = '\"\"\" \"\"\"'

	fnString = "def {} (*args, {}){}: \n\t{}\n\t...".format(
		fnName, argFieldString, rTypeString, docString
	)
	return fnString + "\n\n"


typeAliasMap = {
	"String" : str,
	"Script" : str,
	"Float" : float,
	"Angle" : float,
	"Length" : float,
	"Distance" : float,
	"on|off" : bool,
	"Int" : int,
	"UnsignedInt" : int,
}


def main (module, fp:str):
	members = inspect.getmembers(module)
	members = [i for i in members if not i[0] == "__builtins__"]
	members = tuple(filter(lambda x: not (x[0].startswith("__") and x[0].endswith("__")), members))
	values = module.__dict__.values()


	result = ""

	# import block
	typingImport = "from typing import Tuple, List, Set, Dict"
	imports = [typingImport]
	importBlock = "\n".join(imports) + "\n\n"

	result += importBlock



	for i in members:
		if not callable(i[1]):
		# if not isinstance(i[1], callable):
			continue
		# try:
		#result[i[0]] =  inspect.getfullargspec(i[1])
		try:
			lines = cmds.help(i[0], language="python",)
		except:
			continue

		lines = lines.split("\n")
		#print(lines)
		splitTokens = []
		for line in lines:
			if not line.strip():
				continue

			if not line.strip().startswith("-"):
				continue
			tokens = line.split(" ")

			items = tokens
			items = tuple(filter(lambda x:x, items))


			kwargName = items[1][1:]  # full kwarg name

			if len(items) == 2: # boolean flag
				kwargSig = [bool]

			else: # multiple arguments denotes tuple
				sigNames = items[2:]
				kwargSig = []
				for n in sigNames:
					if n in ("(multi-use)",):
						continue
					#sigMap = { n : typeAliasMap[n] for n in sigNames}
					if not n in typeAliasMap:
						continue
					kwargSig.append(typeAliasMap[n])

			items = (kwargName, kwargSig)

			splitTokens.append(items)

		fnString = formatFunction(i[0],
		                          splitTokens)
		result += fnString

		#result[i[0]] = splitTokens



	# output final string to file
	#result = pformat(result)
	with open(fp, "w") as f:
		f.write(result)
	print("done")

if __name__ == '__main__':
	main(cmds, outputPath)