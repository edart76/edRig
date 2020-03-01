""" temp file to test face setups before the full infrastructure is ready """

from edRig import cmds, om, AbsoluteNode, ECA
from edRig import plug, attr, curve, surface, muscle, dynamics


def faceMuscleSetup():

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
	contractPlugs = []
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
		contractPlugs.append( d + ".contraction")

	loft = surface.loftCurves(loftPlugs)
	scalp = ECA("nurbsSurface", n="scalp_srf")
	scalp.con( loft , "create")
	scalp.parentTo(rigGrp)

	print "browPlugs {}".format(browPlugs)

	# create brow anchor curve
	browAnchor = curve.curveFromCvPlugs(browPlugs, name="frontalisAnchor_crv",
	                                    deg=1, useApi=False)
	browAnchor.transform.parentTo(rigGrp)

	# dynamics
	faceNucleus = dynamics.Nucleus.create(name="faceNucleus")
	faceNucleus.parentTo(rigGrp)
	faceNucleus.set("gravity", 0.5)

	# add skull collider
	faceNucleus.addCollider(mesh="colliders_combined",
	                        name="skull")

	# scalp result
	browMuscle = muscle.MuscleCurve.create(browAnchor,
	                                       nucleus=faceNucleus,
	                                       name="browAnchor",)
	browMuscle.setDepth(0)
	browMuscle.setLockedPoints("none")
	browMuscle.ctrl.first.addAttr(attrName="scalpContract", dv=0, min=0, max=1)
	for i in contractPlugs:
		browMuscle.ctrl.first.con("scalpContract", i)

	# frontalis brow muscles
	frontalisInputs = [
		"frontalis_a",
		"frontalis_b",
		"frontalis_c",
	]
	frontalisMuscles = []
	for i in frontalisInputs:
		frMuscle = muscle.MuscleCurve.create(i,
		                                     nucleus=faceNucleus,
		                                     name=i+"Muscle")
		frontalisMuscles.append(frMuscle)
		frMuscle.setDepth(1)

		# constrain to browAnchor
		frPoint, browPoint = curve.mutualClosestPoints(
			frMuscle.outputShape, browMuscle.outputShape)
		frIndex = round( frMuscle.outputShape.shapeFn.getParamAtPoint(frPoint))
		browIndex = round(browMuscle.outputShape.shapeFn.
		                  getParamAtPoint(browPoint))
		# frComp = frMuscle.hair.getComponent(frIndex)
		# browComp = browAnchor.hair.getComponent(browIndex)

		constraint = dynamics.NConstraint.create(name=i+"_constraint")
		#constraint.connectToNucleus(faceNucleus)
		constraint.constrainElements(elementA=frMuscle.hair,
		                             indexA=frIndex,
		                             elementB=browMuscle.hair,
		                             indexB=browIndex,
		                             nucleus=faceNucleus)


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

