# in framestore, they called me the curve guy
import maya.cmds as cmds
import core as core
from core import ECN, con, AbsoluteNode, ECA
import maya.api.OpenMaya as om
from nodule import nodule
from edRig import utils, attr

def isCurve(node):
	if core.isType(node, "nurbsCurve") or core.isType(node, "bezierCurve"):
		return True
	else:
		return False

def getCurveInfo(shape):
	shape = AbsoluteNode(shape)
	curveInfo = {}
	if isCurve(shape):
		curveInfo = {}
		fn = shape.shapeFn
		curveInfo["cvs"] = [(i.x, i.y, i.z) for i in fn.cvPositions()]
		curveInfo["degree"] = fn.degree
		curveInfo["form"] = fn.form
		curveInfo["knots"] = [i for i in fn.knots()]
		#curveInfo["rational"] = fn.rational()
		curveInfo["rational"] = True

		print "{} info is {}".format(shape, curveInfo)

	else:
		testShape = shape.shape
		if isCurve(testShape):
			return getCurveInfo(testShape)
		else:
			print "it's called getCurveInfo for a reason, {} is not curvy".format(
				shape)
	print "{} info is {}".format(shape, curveInfo)
	return curveInfo

def setCurveInfo(info, target=None, create=True, parent=None):
	"""apply info from dict, or just create anew"""
	fn = om.MFnNurbsCurve()
	target = AbsoluteNode(target)
	target.delete()

	print "info to set is {}".format(info)

	cvs = [om.MPoint(i) for i in info["cvs"]]
	shapeObj = fn.create(
		cvs, info["knots"], info["degree"], info["form"], False, True, parent=parent.MObject
	)
	return shapeObj


def getCurveDiff(base, target):
	baseInfo = getCurveInfo(base)
	targetInfo = getCurveInfo(target)
	baseCvs = baseInfo["cvs"]
	targetCvs = targetInfo["cvs"]
	diffs = []
	if len(baseCvs) != len(targetCvs):
		print "getCurveDiff may not work with different cv numbers"
	for i in range(len(baseCvs)):
		diffs.append([])
		for e in range(3):
			diffs[i].append(targetCvs[i][e] - baseCvs[i][e])
	return diffs

def matchCurve(base, target):
	baseInfo = getCurveInfo(base)
	targetInfo = getCurveInfo(target)
	baseCvs = baseInfo["cvs"]
	print "baseCvs is {}".format(baseCvs)
	targetCvs = targetInfo["cvs"]
	print "targetCvs is {}".format(targetCvs)
	for i in range(len(baseCvs)):
		cmds.move(targetCvs[i][0], targetCvs[i][1], targetCvs[i][2],
			"{}.cv[{}]".format(base, i), a=True, ws=True)
		# for index, ax in enumerate("xyz"):
		#     cmds.setAttr("{}.controlPoints[{}].{}Value".format(base, i, ax),
		#     targetCvs[i][index])


#attach transform to curve
def curveRivet(dag, crv, uVal, upCrv=None, upSpace="world", top=True, rotX=True,
	constantU=True, purpose="anyPurpose", noCycle=True):
	"""purpose parametre allows reuse of point on curve nodes"""

	if noCycle:
		"""we're going to be using this a lot - use network nodes to hold control"""
		ctrl = ECN("network", name="{}-{}-pciCtrl".format(dag, uVal))
		cmds.addAttr(ctrl, ln="uVal", at="double", min=0, dv=uVal, k=True)
		ctrlPlug = ctrl+".uVal"
	else:
		cmds.addAttr(dag, ln="uVal", at="double", min=0, dv=uVal, k=True)
		ctrlPlug = dag + ".uVal"
	pci = ECN("pci", "{}-{}-pci".format(dag, uVal))
	con(crv+".local", pci+".inputCurve")
	con(pci+".position", dag+".translate")
	con(ctrlPlug, pci+".parameter")

	cmds.setAttr(pci+".turnOnPercentage", top)

	aim = ECN("aim", "{}-{}-aimConst".format(dag, uVal))
	cmds.setAttr(aim+".constraintVector", 1,0,0)
	cmds.connectAttr(pci+".normalizedTangent", aim+".target[0].targetTranslate")

	if upCrv:
		upPci = pciAtU(upCrv, uVal, constantU=constantU,
			purpose=purpose, percentage=top)
		#cmds.setAttr(upPci+".turnOnPercentage", top)
		con(ctrlPlug, upPci+".parameter")
		# if upSpace == "local" :
		#     con(upCrv+".local", upPci+".inputCurve")
		# else:
		#     con(upCrv+".worldSpace[0]", pci+".inputCurve")

		cmds.setAttr(aim+".worldUpType", 3) #vector up
		upVec = utils.vecFromTo( upPci+".position", pci+".position")
		con(upVec, aim+".upVector")
	else:
		# just use the normal of the point node
		#cmds.setAttr(aim+".worldUpType", 4) #fucking nothing
		cmds.setAttr(aim+".worldUpType", 3)
		cmds.setAttr(aim+".constraintRotateOrder", 2)
		con(pci+".normalizedNormal", aim+".upVector")
		#con(pci+".normal", aim+".upVector")

	if rotX:
		con(aim+".constraintRotate", dag+".rotate")
	if not rotX:
		con(aim+".constraintRotateY", dag+".rotateY")
		con(aim+".constraintRotateZ", dag+".rotateZ")
	#aint nobody need no frenet frame
	# if we want to get rid of constraints, you can do compose/decompose
	# matrix, but i think here they're fine
	# returns new reference to dag
	return dag



#create nurbs curve through arbitrary points
def curveFromCvs(points, closed=False, deg=3, name="pointCrv",
					mode="static"):
	# adding a live connect mode inside this fuction is so not worth it
	# said the stupid ed of the past
	# mode="live1d" - this is a special case for curve searching
	outCrv = ""
	out = {}
	for i, item in enumerate(points):
		if mode=="static":
			if core.isAttr(item):
				crvPoint = cmds.getAttr(item)[0]
				# this had better be a 3D attribute
				# if you want to plot a 2D curve you have better ways
			else:
				crvPoint = item

		elif mode=="live" or mode=="null" or mode=="live1d":
			# only want a curve of degree and span
			crvPoint = [2*i,0,0]

		#core.debug(crvPoint)
		#core.debug(crvPoint[0])
		if i == 0:
			outCrv = cmds.curve(p=crvPoint,
			worldSpace=True, periodic=0,
			degree=deg, n=name)

		else:
			cmds.curve(outCrv, p=crvPoint,
			worldSpace=True, append=True)

	core.debug(outCrv)
	outCrvShape = cmds.listRelatives(outCrv, shapes=True)
	outCrvShape = cmds.rename(outCrvShape, outCrv+"Shape")

	if mode=="live" or mode=="live1d":
		for i, item in enumerate(points):
			if mode=="live1d":
				cmds.connectAttr(item,
				"{}.controlPoints[{}].yValue".format(outCrvShape, i))
			else:
				con(item, "{}.controlPoints[{}]".format(outCrvShape, i))
				pass
	out["tf"] = outCrv
	out["shape"] = cmds.listRelatives(outCrv, shapes=True)[0]
	return out

def curveBinarySearch(crv, startU, targetLength):
	#supercede that aim feedback loop in carpal

	pass
	#it's time to ascend

def createCurve(name):
	#create a single nurbs curve node (named properly) for data management
	shape = cmds.createNode("nurbsCurve", n=name+"_shape")
	parent = cmds.listRelatives(shape, parent=True)
	transform = cmds.rename(parent, name+"_transform")
	return [shape, transform]

def duplicateCurveTf(tf, name="curveDupe"):
	newTf = cmds.duplicate(tf, n=name, rc=True)
	shape = cmds.listRelatives(newTf, s=True)
	#shape = cmds.rename(shape, "eyyyThisIsTemp")
	shape = cmds.rename(shape, name+"Shape")
	data = {}
	data["tf"] = newTf
	data["shape"] = shape
	return data

def curveFnFrom(curve):
	MObject = core.MObjectFrom(core.shapeFrom(curve))
	curveFn = om.MFnNurbsCurve(MObject)
	# Return result
	return curveFn

def getClosestU(curve, tf):
	#print "u curve is {}".format(curve)
	dummy = None
	if core.isPlug(curve): # create dummy shape node
		curve = ECA("nurbsCurve", "dummyCrv")
		dummy = True
	curveFn = curveFnFrom(curve)
	tfPos = cmds.xform(tf, q=True, ws=True, t=True)
	point = om.MPoint(*tfPos)
	#u = curveFn.closestPoint(point, space=om.MSpace.kWorld)
	u = curveFn.closestPoint(point)[1]
	if dummy:
		cmds.delete(curve.transform)
	return u

def getLiveNearestPoint(curve, tf):
	pass


def pciAtU(crvShape, u=0.1, percentage=True,
	local=True, constantU=True, purpose="anyPurpose"):
	# if there's an alias thing in python i want to call this pikachu
	# check for other pcis attached to the curve to avoid unnecessary usage
	# if it's constant, at the same u, it's compatible
	# if it's not constant, at the same U for a different purpose,

	connectedPcis = cmds.listConnections(crvShape+".local", d=True, s=False,
		type="pointOnCurveInfo")
	testPcis = []
	targetPci = ""
	if connectedPcis:
		for i in connectedPcis:
			if cmds.getAttr(i+".parameter") == u:
				testPcis.append(i)
				break
	print "testPcis is {}".format(testPcis)
	if testPcis:
		for i in testPcis:
			constantTest = attr.getTag(i, tagName="constantU")
			# constantTest = core.Op.getTag(i, tagName = "constantU")
			print "test is {}".format(constantTest)
			if constantU:
				if constantTest == "True":
					targetPci = i
					break
			if not constantU:
				purposeTest = core.Op.getTag(i, tagName="purpose")
				print "purposeTest is {}".format(purpose)
				if constantTest == "False" and purposeTest == purpose:
					targetPci = i
					break
	print "target pci is {}".format(targetPci)

	if not targetPci:
		targetPci = nodule(ECN("pci", "pointOn_{}_at{}u".format(crvShape, str(u))))
		core.Op.addTag(targetPci, "constantU", str(constantU))
		core.Op.addTag(targetPci, "purpose", str(purpose))
		targetPci.parameter = u
		con(crvShape+".local", targetPci+".inputCurve")

	return targetPci


def matrixAtU(crv, u=0.5, percentage=True):
	# x faces down the curve
	pos = cmds.pointOnCurve(crv, top=percentage, p=True, pr=u)
	tan = cmds.pointOnCurve(crv, top=percentage, pr=u, normalizedTangent=True)
	norm = cmds.pointOnCurve(crv, top=percentage, pr=u, normalizedNormal=True)

	posVec = om.MVector(pos)
	tanVec = om.MVector(tan)
	normVec = om.MVector(norm)
	binormVec = (tanVec ^ normVec).normalize()
	binorm = (0,1,0)
	# works

	#mat = om.MMatrix(tanVec, normVec, binormVec, posVec)

	mat = om.MMatrix((tanVec[0], tanVec[1], tanVec[2], 0,
					normVec[0], normVec[1], normVec[2], 0,
					binormVec[0], binormVec[1], binormVec[2], 0,
					posVec[0], posVec[1], posVec[2], 1))
	return mat

def liveMatrixAtU(crvShape, u=0.5, constantU=True, purpose="anyPurpose",
                  upCurve=None):
	data = {}
	pci = pciAtU(crvShape, u=u, constantU=constantU, purpose=purpose)
	mat = ECA("4x4", "matAtU")
	vec = ECA("vp", "biNormal", "cross")
	con(pci+".normalizedTangentX", mat+".in00")
	con(pci+".normalizedTangentY", mat+".in01")
	con(pci+".normalizedTangentZ", mat+".in02")
	mat.in03 = 0
	con(pci+".normalizedNormalX", mat+".in10")
	con(pci+".normalizedNormalY", mat+".in11")
	con(pci+".normalizedNormalZ", mat+".in12")
	mat.in13 = 0

	con(pci+".normalizedTangent", vec+".input1")
	con(pci+".normalizedNormal", vec+".input2")

	con(vec+".outputX", mat+".in20")
	con(vec+".outputY", mat+".in21")
	con(vec+".outputZ", mat+".in22")
	mat.in23 = 0

	con(pci+".positionX", mat+".in30")
	con(pci+".positionY", mat+".in31")
	con(pci+".positionZ", mat+".in32")
	mat.in33 = 1

	data["mat"] = mat
	data["vec"] = vec
	data["pci"] = pci
	return data

#def duplicateShape(shape, search="", replace=""):
# moved to core
