# list of valid ops to make tiles out of

# from edRig.layers.pointlayers import * # look federico
# from edRig.layers.jointlayers import * # it's full of stars
# from edRig.layers.curvelayers import *
# from edRig.layers.surfacelayers import *
# from edRig.layers.misclayers import *
import pprint
from edRig.layers import pointlayers, \
	jointlayers, curvelayers, surfacelayers, misclayers

from edRig.pipeline import safeLoadModule

from edRig.tilepile.ops.op import Op

from edRig.lib.python import itersubclasses, \
	iterSubModuleNames, safeLoadModule

print "opList imported"

#allOps = itersubclasses(Op)

class OpList(object):

	# ops = [
	# 	#0D
	# 	controlop.ControlOp, ikop.IkOp,
	# 	#1D
	# 	JointCurveOp, #VariableFkOp,
	# 	BezierOp,
	# 	#2D
	# 	SkinOp,
	# 	#misc
	# 	ImportDrivenOp, ImportDriverOp, PythonOp,
	# ]

	opPackages = [
		pointlayers,
		jointlayers,
		curvelayers,
		surfacelayers,
		misclayers
	]

	ops = set()

	def __init__(self):
		"""find all known op (real) classes"""
		# first import all packages where op classes might be
		for package in self.opPackages:
			moduleNames = iterSubModuleNames(package=package)
			for moduleName in moduleNames:
				#print "moduleName {}".format(moduleName)
				module = safeLoadModule(moduleName)

		# now load ops
		for op in itersubclasses(Op):
			# for now we skip parent ops - this may not be desired
			if op.__subclasses__() and not op.forceInclude:
				continue
			self.ops.add(op)

		#print (pprint.pformat("ops {}".format(self.ops)))
		#pprint.pprint(self.ops)

		# works for now, just don't sneeze near it

	def __repr__(self):
		return self.ops

ValidList = OpList()

"""we need a better way to import stuff

we know the package - 
	for every included module,
		for every included class,
			if it's a child class of Op,
				add it to ValidList ops"""

