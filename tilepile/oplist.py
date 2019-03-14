# list of valid ops to make tiles out of
from edRig.layers.pointlayers import *
from edRig.layers.jointlayers import *
from edRig.layers.curvelayers import *
from edRig.layers.surfacelayers import *
from edRig.layers.misclayers import *

class OpList(object):

	ops = [
		#0D
		ControlOp,
		#1D
		JointCurveOp, #VariableFkOp,
		BezierOp,
		#2D
		SkinOp,
		#misc
		ImportDrivenOp, ImportDriverOp, PythonOp,
	]

	def __repr__(self):
		return self.ops

ValidList = OpList()
