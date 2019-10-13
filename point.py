

from maya import cmds

from edRig import core, transform, curve, ECA


def getPoint(on=None, near=None, live=True):
	"""blanket catch-all method for getting closest point
	on curves, meshes, surfaces"""
	print "on is {}".format(on)
	plug = None
	if core.isPlug(on):
		plug = getPointFromPlug(on, near)
	return plug

def getPointFromPlug(on, near, up=None):
	"""returns matrix plug"""
	kind = cmds.getAttr(on, type=True)
	mat = None
	if kind == "matrix" :
		# my work is done
		mat = on
	else:
		dummy = ECA("locator", "pointProxy")
		transform.matchXforms(dummy, source=near)
		if kind == "nurbsCurve":
			u = curve.getClosestU(on, near)
			curve.curveRivet(dummy, on, u, upCrv=up)
			mat = dummy +".matrix"
	return mat