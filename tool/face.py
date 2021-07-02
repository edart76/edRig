""" temp file to test face setups before the full infrastructure is ready """

from edRig import cmds, om, EdNode, ECA
from edRig import plug, attr, curve, surface, muscle, dynamics, anim


def faceMuscleSetup():

	if cmds.ls("rig_grp"):
		rigGrp = EdNode("rig_grp")
	else:
		rigGrp = ECA("transform", n="rig_grp")

	baseCurves = [EdNode(i) for i in cmds.listRelatives(
		"L_grp", children=True)]
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
		d = EdNode(cmds.duplicate(i, n=i + "_contract")[0])
		print(d)
		print(cmds.objExists(d))
		cmds.parent(d, rigGrp)
		d.addAttr(attrName="contraction", dv=0, min=0.01, max=0.99)
		d.addAttr(attrName="minLength", dv=0.7, min=0.01, max=0.99)
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

	print("browPlugs {}".format(browPlugs))

	# create brow anchor curve
	browAnchor = curve.curveFromCvPlugs(browPlugs, name="frontalisAnchor_crv",
	                                    deg=1, useApi=False)
	browAnchor.transform.parentTo(rigGrp)

	# dynamics
	faceNucleus = dynamics.Nucleus.create(name="faceNucleus")
	faceNucleus.parentTo(rigGrp)
	faceNucleus.set("gravity", 0.5)

	# add skull collider
	skull = faceNucleus.addCollider(mesh="colliders_combined",
	                        name="skull")
	#skull.set("collide", 0)
	skull.set("selfCollide", 0)
	skull.set("forceField", 1) # along normal
	skull.set("fieldMagnitude", 0.01)

	# scalp result
	scalpMuscle = muscle.MuscleCurve.create(browAnchor,
	                                       nucleus=faceNucleus,
	                                       name="browAnchor",)
	scalpMuscle.setDepth(0)
	scalpMuscle.setLockedPoints("none")
	scalpMuscle.ctrl.first.addAttr(attrName="scalpContract", dv=0, min=0, max=1)
	for i in contractPlugs:
		scalpMuscle.ctrl.first.con("scalpContract", i)

	# frontalis brow muscles
	frontalisInputs = [
		"frontalis_a",
		"frontalis_b",
		"frontalis_c",
	]
	frontalisMuscles = []
	constraints = []
	constraintSettings = {
		"constraintMethod" : "spring",
		"restLengthMethod" : "constant",
		"damp" : 10,
	}


	# hardcode and duplicate everything for now
	frontalisAM = muscle.MuscleCurve.create("frontalis_a",
		                                     nucleus=faceNucleus,
		                                     name="frontalis_a"+"Muscle")
	frontalisBM = muscle.MuscleCurve.create("frontalis_b",
		                                     nucleus=faceNucleus,
		                                     name="frontalis_b"+"Muscle")
	frontalisCM = muscle.MuscleCurve.create("frontalis_c",
	                                        nucleus=faceNucleus,
	                                        name="frontalis_c" + "Muscle")
	frontalisMuscles = [ frontalisAM, frontalisBM, frontalisCM]

	# corrugator
	corrugatorAM = muscle.MuscleCurve.create("corrugator_a", nucleus=faceNucleus,
	                                        name="corrugator_a" + "Muscle")

	# oculi
	oculiAM = muscle.MuscleCurve.create("oculi_a", nucleus=faceNucleus,
	                                        name="oculi_a" + "Muscle",
	                                    jointRes=7, isRing=True)
	oculiAM.ctrl.first.set("baseSpans", 8)
	oculiBM = muscle.MuscleCurve.create("oculi_b", nucleus=faceNucleus,
	                                    name="oculi_b" + "Muscle",
	                                    jointRes=7, isRing=True)
	oculiBM.ctrl.first.set("baseSpans", 8)

	allMuscles = [
		scalpMuscle,
		frontalisAM, frontalisBM, frontalisCM,
		corrugatorAM,
		oculiAM, oculiBM
	]
	for i in allMuscles:
		i.setUpSolver("surfaceNormal", "skull_collider_hi_res")



	#for i in frontalisInputs:
	for frMuscle in frontalisMuscles:
		# frMuscle = muscle.MuscleCurve.create(i,
		#                                      nucleus=faceNucleus,
		#                                      name=i+"Muscle")
		#frontalisMuscles.append(frMuscle)
		frMuscle.setDepth(1)

		# constrain to browAnchor
		frPoint, browPoint = curve.mutualClosestPoints(
			frMuscle.outputShape, scalpMuscle.outputShape)
		frIndex = round( frMuscle.outputShape.shapeFn.getParamAtPoint(frPoint))
		browIndex = round(scalpMuscle.outputShape.shapeFn.
		                  getParamAtPoint(browPoint))

		constraint = dynamics.NConstraint.create(name=frMuscle.name+"_constraint")
		constraint.constrainElements(elementA=frMuscle.hair,
		                             indexA=frIndex,
		                             elementB=scalpMuscle.hair,
		                             indexB=browIndex,
		                             nucleus=faceNucleus)

		# constraint dynamics
		constraint.set(multi=constraintSettings)

		constraints.append(constraint)

	# bind all joints in basic manner and apply deformers
	outputGeo = "head"
	joint = ECA("joint", n="skinRoot", parent="rigGrp")
	#skc = cmds.skinCluster( joint, outputGeo)

	bindJnts = [joint]
	for i in allMuscles:
		bindJnts.extend(i.joints)
	skc = cmds.skinCluster( bindJnts, outputGeo)
	dm = cmds.deformer( outputGeo, type="deltaMush")




	# common settings
	for i in allMuscles:
		i.ctrl.first.set("damp", 50)


	# make keyframes for test animation
	anim.keyPlug( scalpMuscle.ctrl.first + ".scalpContract", 24, 0)
	anim.keyPlug( scalpMuscle.ctrl.first + ".scalpContract", 200, 1)


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

