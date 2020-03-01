""" temp file to test face setups before the full infrastructure is ready """

from edRig import cmds, om, AbsoluteNode, ECA
from edRig import plug, attr, curve, surface, muscle, dynamics


def faceSetup():

	if cmds.ls("rig_grp"):
		rigGrp = AbsoluteNode("rig_grp")
	else:
		rigGrp = ECA("transform", n="rig_grp")

	baseCurves = [AbsoluteNode(i) for i in cmds.listRelatives(
		"L_grp", children=True) ]
	for i in baseCurves:
		# print type(i)
		# print i
		# print type(i.shape)
		# print i.shape
		i.shape.set("dispCV", 1)

	# occipitalis muscle
	contractCurves = [
		"occipitalis_a",
		"occipitalis_b",
		"occipitalis_c",
	]
	loftPlugs = []
	browPlugs = []
	for i in contractCurves:
		d = AbsoluteNode(cmds.duplicate(i, n=i + "_contract")[0])
		print d
		print cmds.objExists(d)
		cmds.parent(d, rigGrp)
		d.addAttr(attrName="contraction", dv=0, min=0.01, max=0.99)
		d.addAttr(attrName="minLength", dv=0.4, min=0.01, max=0.99)
		p = makeSubCurveContraction( i + ".local",
		                         d + ".minLength",
		                         d + ".contraction",
		                         )
		d.con( p, "create")
		loftPlugs.append(d + ".local")

		# points for brow anchor curve
		pci = curve.pciAtU(d.shape + ".local", u=1.0)
		browPlugs.append( pci + ".result.position")

	loft = surface.loftCurves(loftPlugs)
	scalp = ECA("nurbsSurface", n="scalp_srf")
	scalp.con( loft , "create")
	scalp.parentTo(rigGrp)

	print "browPlugs {}".format(browPlugs)

	# create brow anchor curve
	browAnchor = curve.curveFromCvPlugs(browPlugs, name="frontalisAnchor_crv",
	                                    deg=1, useApi=False)
	browAnchor.transform.parentTo(rigGrp)

	# frontalis and brow setup
	# dynamics
	faceNucleus = dynamics.Nucleus.create(name="faceNucleus")
	faceNucleus.parentTo(rigGrp)

	browMuscle = muscle.MuscleCurve.create(browAnchor,
	                                       nucleus=faceNucleus,
	                                       name="browAnchor",)
	browMuscle.setDepth(0)



	# set out layer structure of muscles
	anchors = [ # these have cv0 anchored on bone (or nearest point)
		"buccinator",
		"mentalis"
	]






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

