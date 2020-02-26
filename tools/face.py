""" temp file to test face setups before the full infrastructure is ready """

from edRig import cmds, om, AbsoluteNode, ECA
from edRig import plug, attr, curve, surface


def faceSetup():
	contractCurves = [
		"occipitalis_a",
		"occipitalis_b",
		"occipitalis_c",
	]
	loftPlugs = []
	for i in contractCurves:
		d = AbsoluteNode(cmds.duplicate(i, n=i + "_contract")[0])
		cmds.parent(d, "rig_grp")
		d.addAttr(attrName="contraction", dv=0)
		d.addAttr(attrName="minLength", dv=0.4)
		p = makeSubCurveContraction( i + ".local",
		                         d + ".minLength",
		                         d + ".contraction",
		                         )
		d.con( p, "create")
		loftPlugs.append(d + ".local")

	loft = surface.loftCurves(loftPlugs)
	scalp = ECA("nurbsSurface", n="scalp_srf")
	scalp.con( loft , "create")






def makeSubCurveContraction(baseCurvePlug, minPlug, contractionPlug):
	""""""
	one = ECA( "addDoubleLinear", n="one" )
	one.set("input1", 1)
	bta = ECA( "blendTwoAttr")
	bta.con( one + ".output", "input[0]")
	bta.conOrSet( minPlug , "input[1]")
	bta.conOrSet( contractionPlug , "attributesBlender")

	s = ECA("subCurve")
	s.con(bta + ".output", "maxValue")
	s.con(baseCurvePlug, "inputCurve")
	s.set("relative", 1)

	r = ECA("rebuildCurve")
	r.con(s + ".outputCurve", "inputCurve")
	r.set("spans", 4)

	return r + ".outputCurve"

