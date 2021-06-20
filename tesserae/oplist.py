# list of valid ops to make tiles out of

# from edRig.layers.pointlayers import * # look federico
# from edRig.layers.jointlayers import * # it's full of stars
# from edRig.layers.curvelayers import *
# from edRig.layers.surfacelayers import *
# from edRig.layers.misclayers import *
import pprint, os, ast

from edRig.tesserae import layers

from edRig.tesserae.layers import pointlayers, \
	curvelayers, surfacelayers, misclayers, \
	dynamiclayers


from edRig.tesserae.ops.op import Op

from edRig.lib.python import itersubclasses, \
	iterSubModuleNames, safeLoadModule

from edRig import ROOT_PATH

print((layers.__file__))
layerDir = os.path.dirname(layers.__file__)

layerModuleNames = ("pointlayers", "curvelayers",
                    "surfacelayers", "misclayers",
                    "dynamiclayers")


def classDataFromAST(baseAstNode):
	"""return {className : {"bases" : [list of base names],
							"path" : string path of file)
				)
	"""
	result = {}
	for classItem in [n for n in baseAstNode.body
	                  if isinstance(n, ast.ClassDef)]:
		className = classItem.name
		result[className] = {"bases" :
			[n.id if isinstance(n, ast.Name) else (
				# attributes returned on "layer.LayerOp" for example
				# 'LayerOp', 'layer', ast.Load
				#(n.attr, n.value.id, n.ctx) if isinstance(n, ast.Attribute)
				n.attr if isinstance(n, ast.Attribute)
				else None)
			 for n in classItem.bases ],
		                     }
	return result



for i in layerModuleNames:
	scanDir = os.path.join(layerDir, i)
	print(scanDir)
	classes = []
	for scanFile in os.listdir(scanDir):
		if not scanFile.endswith(".py"):
			continue
		scanFile = os.path.join(scanDir, scanFile)
		#print(scanFile)

		with open(scanFile) as f:
			astNode = ast.parse(f.read())

		# print classes
		classData = classDataFromAST(astNode)
		pprint.pprint(classData)
		# opClasses = [n for n in foundClasses if "Op" in n.bases]
		#
		# classes.extend(opClasses)
	print(classes)



class OpList(object):

	opPackages = [
		pointlayers,
		#jointlayers,
		curvelayers,
		surfacelayers,
		misclayers,
		dynamiclayers,
	]

	ops = set()

	def __init__(self):
		"""find all known op (real) classes"""
		# first import all packages where op classes might be
		for package in self.opPackages:
			print(package)
			moduleNames = iterSubModuleNames(
				package=package, debug=True)
			print(moduleNames)
			for moduleName in moduleNames:
				#print ("moduleName {}".format(moduleName))
				module = safeLoadModule(moduleName)

		# now load ops
		for op in itersubclasses(Op):
			# for now we skip parent ops - this may not be desired
			# if op.__subclasses__() and not op.forceInclude:
			# 	continue
			self.ops.add(op)

		print (pprint.pformat("ops {}".format(self.ops)))
		#pprint.pprint(self.ops)

		# works for now, just don't sneeze near it

	def __repr__(self):
		return self.ops

ValidList = OpList()
print("opList imported")

"""we need a better way to import stuff

we know the package - 
	for every included module,
		for every included class,
			if it's a child class of Op,
				add it to ValidList ops"""

