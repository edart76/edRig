# s o o n
from maya import cmds
import maya.api.OpenMaya as om
from edRig.core import AbsoluteNode, ECA


def getSurfaceInfo(shape):
	"""return info necessary to reconstruct surface"""
	surfInfo = {}
	fn = shape.shapeFn
	surfInfo["cvs"] = [(i.x, i.y, i.z) for i in fn.cvPositions()]
	surfInfo["uKnots"] = fn.numKnotsInU
	surfInfo["vKnots"] = fn.numKnotsInV
	surfInfo["uDegree"] = fn.degreeInU
	surfInfo["vDegree"] = fn.degreeInV
	surfInfo["uForm"] = fn.formInU
	surfInfo["vForm"] = fn.formInV
	surfInfo["rational"] = True
	return surfInfo
	pass


def setSurfaceInfo(info, target=None, create=True, parent=None):
	"""apply info from dict, or just create anew"""
	fn = om.MFnNurbsSurface()
	target = AbsoluteNode(target)
	target.delete()

	print "info to set is {}".format(info)

	cvs = [om.MPoint(i) for i in info["cvs"]]
	shapeObj = fn.create(
		cvs,
		info["uKnots"],
		info["vKnots"],
		info["uDegree"],
		info["vDegree"],
		info["uForm"],
		info["vForm"],
		info["rational"],
		parent=parent,
	)
	return shapeObj


"""
create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm,
    rational, parent=kNullObj) -> MObject
    * cvs (MPointArray or seq of MPoint)
      - The control vertices.
* uKnots (MDoubleArray or seq of float)
      - Parameter values for the knots in the U direction.
* vKnots (MDoubleArray or seq of float)
      - Parameter values for the knots in the V direction.
* uDegree   (int) - Degree of the basis functions in the U direction.
* vDegree   (int) - Degree of the basis functions in the V direction.
* uForm     (int) - A Form constant (kOpen, kClosed, kPeriodic) giving
        the surface's form in the U direction.
* vForm     (int) - A Form constant (kOpen, kClosed, kPeriodic) giving
        the surface's form in the V direction.
* rational (bool) - Create as rational (True) or non-rational (False)
        surface.
"""
