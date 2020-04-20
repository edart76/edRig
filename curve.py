# in framestore, they called me the curve guy
import maya.cmds as cmds
import core as core
from core import ECN, con
from edRig.node import AbsoluteNode, ECA
import maya.api.OpenMaya as om
from edRig import attr, plug
from edRig.plug import conOrSet

import pprint

sceneScale = 1
# for later

class NurbsCurve(AbsoluteNode):
	"""is this a mistake"""



def isCurve(node):
	if core.isType(node, "nurbsCurve") or core.isType(node, "bezierCurve"):
		return True
	else:
		return False

def makeLine(name):
	"""makes a basic nurbs curve"""
	newCurve = AbsoluteNode(cmds.curve(point=[(0,0,0), (0, sceneScale, 0)],
	                                   degree=1))
	# i love not being able to name a curve when you create it
	newCurve.name = name
	return newCurve

def rebuildCurve(curve, **kwargs):
	curve = AbsoluteNode(curve).shape
	return cmds.rebuildCurve(curve, **kwargs)




def getCurveInfo(shape=None, fn=None):
	"""gather information to regenerate nurbs curve from data"""
	curveInfo = {}
	if isCurve(shape) and not fn:
		shape = AbsoluteNode(shape)
		fn = shape.shapeFn

	curveInfo["cvs"] = [(i.x, i.y, i.z) for i in fn.cvPositions()]
	curveInfo["degree"] = fn.degree
	curveInfo["form"] = fn.form
	curveInfo["knots"] = [i for i in fn.knots()]
	#curveInfo["rational"] = fn.rational()
	curveInfo["rational"] = True
	#print "{} info is {}".format(shape, curveInfo)
	return curveInfo

def setCurveInfo(info, target=None, create=True, parent=None, fn=None):
	"""apply info from dict, or just create anew"""

	fn = om.MFnNurbsCurve()
	target = AbsoluteNode(target)
	targetName = target.name

	parentTf = cmds.createNode("transform", n="tempCurveRecall_tf")

	#print "info to set is {}".format(info)

	cvs = [om.MPoint(i) for i in info["cvs"]]
	shapeObj = fn.create(
		cvs, info["knots"], info["degree"], info["form"], False, True,
		parent=core.MObjectFrom(parentTf)
	)
	# connect attr to maintain references
	dfn = om.MFnDependencyNode( shapeObj )
	shape = AbsoluteNode(dfn.name())
	cmds.connectAttr(shape + ".local", target + ".create", f=True)
	try:
		cmds.getAttr(target + ".local")
	except:
		pass

	#raise RuntimeError

	shape.transform.delete()

	return target


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

def getLengthRatio(crv, uFraction):
	"""retrieve arc length ratio"""
	fn = AbsoluteNode(crv).shapeFn
	return uFraction



#attach transform to curve
def curveRivet(dag, crv, uVal, upCrv=None, upDag=None,
               upSpace="world", top=True, rotX=True,
               byLength=True, upVectorSource=None,
               constantU=True, purpose="anyPurpose", noCycle=True,
               tidyGrp=None):
	"""purpose parametre allows reuse of point on curve nodes"""

	#pci = ECA("pci", "{}-{}-pci".format(dag, uVal))
	crvPlug = crv+".local"
	pci = pciAtU(crvPlug=crvPlug, u=uVal, percentage=top,
	             constantU=constantU,
	             purpose=purpose )
	con(pci + ".position", dag + ".translate")

	if byLength and top:
		"""retrieve a ratio which is correct for the curve length"""

	cmds.setAttr(pci + ".parameter", uVal)
	if not constantU:
		if noCycle:
			"""we're going to be using this a lot - use network nodes to hold control"""
			ctrl = ECN("network", name="{}-{}-pciCtrl".format(dag, uVal))
			cmds.addAttr(ctrl, ln="uVal", at="double", min=0, dv=uVal, k=True)
			ctrlPlug = ctrl+".uVal"
		else:
			cmds.addAttr(dag, ln="uVal", at="double", min=0, dv=uVal, k=True)
			ctrlPlug = dag + ".uVal"
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
		upVec = plug.vecFromTo( upPci+".position", pci+".position")
		con(upVec, aim+".upVector")

	elif upDag:
		""" use provided transform as up vector """
		con(upDag + ".worldMatrix[0]", aim+".worldUpMatrix")
		cmds.setAttr(aim+".worldUpType", 1) # object up

	elif upVectorSource:
		""" use provided tuple or plug as up vector """
		attr.setAttr(aim + ".worldUpType", "vector")
		attr.conOrSet(upVectorSource, aim + ".worldUpVector")

	else:
		# just use the normal of the point node
		attr.setAttr(aim+".worldUpType", "vector")
		attr.setAttr(aim+".constraintRotateOrder", 2)
		con(pci+".normalizedNormal", aim+".worldUpVector")
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
	if tidyGrp:
		cmds.parent(aim, tidyGrp)
	# else:
	# 	cmds.parent(aim, dag)

	# add uValue attribute to riveted transform
	cmds.addAttr(dag, ln="uValue")
	cmds.connectAttr(pci + ".parameter", dag + ".uValue")

	return pci


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
	return AbsoluteNode(outCrvShape)

def curveFromCvPlugs(plugs, closed=False, deg=1, name="pointCrv", useApi=True):
	""" improved rewrite of above to explicitly deal with plugs """
	print( "cvPlugs {}".format(plugs))
	startSpans = len(plugs) - 1
	base = createBaseCurve(name, useApi=0, nPoints=startSpans+1)

	# had ridiculous issues trying to rebuild a linear curve from 2 to 3 points
	cmds.rebuildCurve(base(), degree=deg, ch=0, keepControlPoints=1
	                  )
	for i in range(len(plugs)):
		base.conOrSet( plugs[i], base.shape + ".controlPoints[{}]".format(i))

	return base



def createBaseCurve(name, useApi=True, nPoints=3):
	""" create nurbs curve using shapeFn, cvs at x0 and x1
	:returns AbsoluteNode"""
	if useApi:
		points = [om.MPoint(0, 0, 0,), om.MPoint(1, 0, 0)]
		fn = om.MFnNurbsCurve()
		newObj = fn.create(points, # cvs
		                                 [0.0, 1.0], # knots
		                                 1, # degree
		                                 om.MFnNurbsCurve.kOpen, # form, kOpen
		                                 False, # is2D
		                                 True) # isRational
		node = AbsoluteNode.fromMObject(newObj)

	else:
		node = cmds.curve(p=[(0, 0, 0)],
		                  worldSpace=True, periodic=0,
		                  degree=1, n=name)
		points = [(i,0,0) for i in range( nPoints)]
		for i in range(1, nPoints):
			cmds.curve(node, p=[points[i]], worldSpace=True, append=True)
		node = AbsoluteNode(node)

	node = AbsoluteNode(node.rename(name))
	return node.transform


def curveBinarySearch(crv, startU, targetLength):
	#supercede that aim feedback loop in carpal

	pass
	#it's time to ascend

def createCurve(name, init=True):
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

def arcLength(curve):
	if isinstance(curve, AbsoluteNode):
		return curve.shape.shapeFn.length()
	else:
		return cmds.arcLen(curve, ch=False)

def getClosestU(curve, tf):
	#print "u curve is {}".format(curve)
	dummy = None
	if core.isPlug(curve): # create dummy shape node
		dummyCurve = ECA("nurbsCurve", "dummyCrv")
		dummy = True
		curve.con(curve, dummyCurve.inShape)
		curve = dummyCurve
	curveFn = curveFnFrom(curve)
	tfPos = cmds.xform(tf, q=True, ws=True, t=True)
	point = om.MPoint(*tfPos)
	#u = curveFn.closestPoint(point, space=om.MSpace.kWorld)
	u = curveFn.closestPoint(point)[1]
	if dummy:
		cmds.delete(curve.transform)
	return u

def rebuildCurve(plug, name="rebuild"):
	""" inserts rebuildCurve node on target plug"""
	node = ECA("rebuildCurve", n=name)
	node.con(plug, "inputCurve")
	return node




def getLiveNearestPoint(curve, tf):
	pass


def pciAtU(crvPlug, u=0.1, percentage=True,
	constantU=True, purpose="anyPurpose"):
	""" low level function to produce a point on a curve """
	# check for other pcis attached to the curve to avoid unnecessary usage
	# if it's constant, at the same u, it's compatible
	# if it's not constant, at the same U for a different purpose, not

	crvName=crvPlug.split(".")[0]

	# first look through all connected pci nodes
	connectedAll = attr.getImmediateFuture(crvPlug)
	connectedPcis = [i for i in connectedAll
	                 if cmds.nodeType(i) == "pointOnCurveInfo"]
	testPcis = []
	targetPci = ""
	for i in connectedPcis:
		if cmds.getAttr(i+".parameter") == u:
			testPcis.append(i)
			#break

	# can any pcis be reused?
	for i in testPcis:
		constantTest = attr.getTag(i, tagName="constantU")
		# constantTest = core.Op.getTag(i, tagName = "constantU")
		#print "test is {}".format(constantTest)
		if constantU:
			if constantTest == "True":
				targetPci = i
				break
		if not constantU:
			purposeTest = attr.getTag(i, tagName="purpose")
			print("pci purposeTest is {}".format(purpose))
			if constantTest == "False" and purposeTest == purpose:
				targetPci = i
				break

	# create new pci node
	if not targetPci:
		uStr = str(u).replace(".", "o")[:3]
		targetPci = ECN("pci", crvName+"_pointAt_{}u".format( uStr ))
		attr.addTag(targetPci, "constantU", str(constantU))
		attr.addTag(targetPci, "purpose", str(purpose))
		cmds.setAttr(targetPci + ".parameter", u)
		con(crvPlug, targetPci+".inputCurve")
		cmds.setAttr(targetPci + ".turnOnPercentage", int(percentage))

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

def matrixPlugFromPci(pci, upVector=None):
	""" more atomic rewrite of curve functions using clear plug
	:param pci : AbsoluteNode
	:param upVector : tuple or plug"""

	mat = ECA("4x4", "matAtU")
	vp = ECA("vp", "biNormal", "cross")

	con(pci+".normalizedTangent", vp + ".input1")

	if upVector:
		conOrSet( upVector, vp + ".input2")
	else:
		con(pci + ".normalizedNormal", vp + ".input2")

	sources = [pci + ".normalizedTangent",
	           pci + ".normalizedNormal",
	           vp + ".output",
	           pci + ".position",]

	for source, row in zip(sources, "0123"):

		for ax, column in zip("XYZ", "012"):
			con( source + ax,
			     mat + ".in" + row + column)

	return mat + ".output"


def liveMatrixAtU(crvShape, u=0.5, constantU=True, purpose="anyPurpose",
                  upCurve=None):
	"""plug-agnostic since we call pciAtU
	deprecated for more clear plug interfaces"""
	data = {}
	pci = pciAtU(crvShape, u=u, constantU=constantU, purpose=purpose)

	mat = ECA("4x4", "matAtU")
	vec = ECA("vp", "biNormal", "cross")

	con(pci+".normalizedTangentX", mat+".in00")
	con(pci+".normalizedTangentY", mat+".in01")
	con(pci+".normalizedTangentZ", mat+".in02")
	mat.set("in03", 0)

	if upCurve:
		"""use upcurve vector instead of flaky normal"""
		if not attr.isPlug(upCurve):
			upCurve = upCurve+".local"
		upPci = pciAtU(upCurve, u=u, constantU=constantU,
		               purpose=purpose)
		upVec = plug.vecFromTo(pci+".position", upPci+".position")
		for ax, i in zip("XYZ", (0,1,2)):
			con(upVec+"ax", mat+".in1{}".format(i) )
			con(upVec, vec + ".input2")

	else:
		con(pci+".normalizedNormalX", mat+".in10")
		con(pci+".normalizedNormalY", mat+".in11")
		con(pci+".normalizedNormalZ", mat+".in12")
		con(pci + ".normalizedNormal", vec + ".input2")

	mat.set("in13", 0)
	con(pci+".normalizedTangent", vec+".input1")

	con(vec+".outputX", mat+".in20")
	con(vec+".outputY", mat+".in21")
	con(vec+".outputZ", mat+".in22")
	mat.set("in23", 0)

	con(pci+".positionX", mat+".in30")
	con(pci+".positionY", mat+".in31")
	con(pci+".positionZ", mat+".in32")
	mat.set("in33", 0)

	data["mat"] = AbsoluteNode(mat)
	data["vec"] = vec
	data["pci"] = pci
	return data

def staticClosestPoint(curve, point):
	""" uses api to find closest point on curve """
	curve = AbsoluteNode(curve)
	point = om.MPoint(point)
	closestPoint, closestU = curve.shapeFn.closestPoint(point)
	return closestPoint, closestU



def mutualClosestPoints( curveA, curveB, steps=5 ):
	""" find points of closest approach between two curves """
	curveA = AbsoluteNode(curveA)
	curveB = AbsoluteNode(curveB)
	point = curveB.shapeFn.getPointAtParam(0.5)
	for i in range(steps):
		point = staticClosestPoint(curveA, point)[0]
		pointA = point
		point = staticClosestPoint(curveB, point)[0]
		pointB = point
	return pointA, pointB

# def cvFromU( curve, uValue ):
# 	""" returns the closest cv to a full uValue """




