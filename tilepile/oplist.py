# list of valid ops to make tiles out of
from edRig.layers.pointlayers import pointop,\
	controlop, ikop, aimop
from edRig.layers.jointlayers import *
from edRig.layers.curvelayers import *
from edRig.layers.surfacelayers import *
from edRig.layers.misclayers import *

from edRig.tilepile.ops.op import Op

class OpList(object):

	ops = [
		#0D
		controlop.ControlOp, ikop.IkOp,
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

"""we need a better way to import stuff

we know the package - 
	for every included module,
		for every included class,
			if it's a child class of Op,
				add it to ValidList ops"""

