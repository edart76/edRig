# move stuff around
import edRig.node
from edRig import core, attr, cmds, om, con
from core import ECN
from edRig.node import AbsoluteNode, ECA


import math

# def matchTransforms(target=None, source=None, pos=True, rot=True):
#     sourceFn = core.MFnTransformFrom(source)
#     sourceMatFn = sourceFn.transformation()
#     matchMatrix(target, sourceMatFn, pos=pos, rot=rot)

def matchXforms(target=None, source=None, pos=True, rot=True):
	if pos:
		trans = cmds.xform(source, q=True, ws=True, t=True)
		cmds.xform(target, ws=True, t=trans)
	if rot:
		rotation = cmds.xform(source, q=True, ws=True, ro=True)
		cmds.xform(target, ws=True, ro=rotation)

# def staticAxisFromTransform(dag, ax=(1,0,0), length=5):
#     mat = cmds.getAttr(dag+".worldMatrix[0]")
#     return mat * ax
	# mat = core.MMatrixFrom(dag)
	# return staticVecMatrixMult(mat, point=ax, length=length)
def MMatrixFromValues(vals):
	return matrixFromValues(vals)

def matrixFromValues(vals):
	"""return an MMatrix from sequence of floats"""
	if not (len(vals) == 16 or len(vals) == 4):
		raise RuntimeError("wrong number of values supplied to matrix")
	return om.MMatrix(vals)

def MMatrixFromPlug(plug):
	return matrixFromPlug(plug)

def valuesFromMatrix(mat):
	vals = []
	rows = [0,1,2,3]
	columns = [0,1,2,3]
	for row in rows:
		for column in columns:
			vals.append(mat.getElement(row, column))
	return vals

def fourByFourFromValues(vals, name, plug=True):
	"""creates a static fourByFourMatrix node from mmatrix
	for use as static offset"""
	mat = ECA("fourByFourMatrix", name=name)
	plugs = getFourByFourInputs(mat)
	for i, val in enumerate(vals):
		cmds.setAttr(plugs[i], val)
	return mat+".output" if plug else mat

def fourByFourFromPlugs(plugs, name="constructedMat"):
	"""base atomic function taking list of plugs and returning 4x4 matrix
	could also use composeMatrix but this gives more control"""
	assert isinstance(plugs, list)
	assert len(plugs) == 16
	mat = ECA("fourByFourMatrix", name=name)
	matPlugs = getFourByFourInputs(mat)
	for i, val in enumerate(plugs):
		if not val:
			continue
		cmds.connectAttr(val, matPlugs[i])
	return mat

def fourByFourFromCompoundPlugs(xPlug=None, yPlug=None, zPlug=None, posPlug=None,
                                name="constructedMat"):
	""" usually we have plug compounds for each axis
	also this is hardcoded to XYZ child names, rip"""
	mat = ECA("fourByFourMatrix", n=name)
	sources = [xPlug, yPlug, zPlug, posPlug]
	for source, row in zip(sources, "0123"):
		if not source : continue
		for ax, column in zip("XYZ", "012"):
			if isinstance(source, tuple):
				sourcePlug = source[ int( column ) ]
			else: sourcePlug = source + ax
			con( sourcePlug,
			     mat + ".in" + row + column)
	return mat + ".output"

def getFourByFourInputs(matNode=None):
	"""maps 0-15 index to annoying 01 - 31 plug naming"""
	matNode = matNode or ""
	rank = 4
	plugs = []
	for i in range(rank): # rows
		for n in range(rank): # columns
			plugs.append(matNode+".in{}{}".format(i, n))
	return plugs


def fourByFourFromMatrix(mat, name, plug=True):
	vals = valuesFromMatrix(mat)
	return fourByFourFromValues(vals, name, plug)

def matrixFromPlug(plug):
	"""returns MMatrix with same values as matrix plug"""
	vals = cmds.getAttr(plug)
	return matrixFromValues(vals)

def getMatrixOffset(a, b):
	"""difference between two mmatrices"""
	return a * b.inverse()

def getMatrixPlugOffset(a, b):
	aMat = matrixFromPlug(a)
	bMat = matrixFromPlug(b)
	return getMatrixOffset(aMat, bMat)

def pointFrom(source):
	"""returns an MPoint from existing MPoint, tuple, or object's transforms"""
	if isinstance(source, om.MPoint):
		return source
	try:
		return om.MPoint(source)
	except: # it's a node
		return AbsoluteNode(source).worldPos()

def blendTwoMatrixPlugs(a, b, weight=0.5):
	"""creates a wtAddMatrix node and connects up matrix plugs, either static or live blend"""
	blend = ECA("wtAddMatrix", name="matrixBlend")
	cmds.connectAttr(a, blend+".wtMatrix[0].matrixIn")
	cmds.connectAttr(b, blend + ".wtMatrix[1].matrixIn")
	if isinstance(weight, basestring): # it's a plug
		weightB = getReverseOfPlug(weight)
		cmds.connectAttr(weight, blend + ".wtMatrix[0].weightIn")
		cmds.connectAttr(weightB, blend + ".wtMatrix[1].weightIn")
	elif isinstance(weight, tuple):
		cmds.connectAttr(weight[0], blend + ".wtMatrix[0].weightIn")
		cmds.connectAttr(weight[1], blend + ".wtMatrix[1].weightIn")
	else:
		cmds.setAttr(blend+".wtMatrix[0].weightIn", weight)
		cmds.setAttr(blend + ".wtMatrix[1].weightIn", 1.0 - weight)
	return blend+".matrixSum" # AND THE BLENDER ATTRIBUTES


def getReverseOfPlug(plug):
	"""shouldn't be in transform but it fits
	returns plug of 1 - input plug"""
	rev = ECA("reverse", "reverse")
	cmds.connectAttr(plug, rev+".inputX")
	return rev+".outputX"

def isMatrix(plug):
	return cmds.getAttr(plug, type=True) == "matrix"


def WorldMMatrixFrom(dag):
	"""exact same as core, but should be in this module"""
	return core.MMatrixFrom(dag)

def staticVecMatrixMult(mat, point=(1,0,0), length=1):
	startPoint = om.MPoint(*point)
	mat = om.MMatrix(mat)
	endPoint = startPoint * mat
	print ""
	print "endPoint is {}".format(endPoint)
	return endPoint.x, endPoint.y, endPoint.z

def matchMatrix(transform, matchMat, pos=True, rot=True):
	# self-explanatory
	space = om.MSpace.kWorld
	#mat = matchMat
	if core.isNode(matchMat):
		# this is very handy as a faster alternative to cmds version
		matchMat = matchMat
	mat = om.MTransformationMatrix(matchMat)

	print "transform is {}".format(transform)
	tFn = core.MFnTransformFrom(transform)
	print "tFn is {}".format(tFn)
	if pos:
		trans = om.MVector(mat.translation(4))
		print "trans is {}".format(trans)
		tFn.setTranslation(trans, om.MSpace.kTransform)
	if rot:
		rot = mat.rotation(space)
		tFn.setRotation(rot, om.MSpace.kTransform)

def matchTransformation(targetNode, followerNode, translation=True, rotation=True):
	followerMTransform = AbsoluteNode(followerNode).MFnTransform
	targetMTransform = AbsoluteNode(targetNode).MFnTransform
	targetMTMatrix = om.MTransformationMatrix(om.MMatrix(cmds.xform(targetNode, matrix=True, ws=1, q=True)))
	if translation:
		targetRotatePivot = om.MVector(targetMTransform.rotatePivot(om.MSpace.kWorld))
		followerMTransform.setTranslation(targetRotatePivot, om.MSpace.kWorld)
	if rotation:
		# using the target matrix decomposition
		# Worked on all cases tested
		followerMTransform.setRotation(targetMTMatrix.rotation(True), om.MSpace.kWorld)

	# Using the MFnTransform quaternion rotation in world space
	# Doesn't work when there is a -1 scale on the object itself
	# Doesn't work when the object has frozen transformations and there is a -1 scale on a parent group.
	# followerMTransform.setRotation(MFntMainNode.rotation(OpenMaya.MSpace.kWorld, asQuaternion=True),OpenMaya.MSpace.kWorld)
# thank you Riham Toulan ^-^


def buildMatrix(translate=(0,0,0),xAxis=(1,0,0),yAxis=(0,1,0),zAxis=(0,0,1)):
	# fingers are thanking me
	mat = om.MMatrix((
					xAxis[0], xAxis[1], xAxis[2], 0,
					yAxis[0], yAxis[1], yAxis[2], 0,
					zAxis[0], zAxis[1], zAxis[2], 0,
					translate[0], translate[1], translate[2], 1
	))
	return mat


def liveDistanceBetweenPoints(pointAttrA, pointAttrB, name="distanceBetween", mode="3d"):
	pointA = core.nodeFromAttr(pointAttrA)
	pointB = core.nodeFromAttr(pointAttrB)
	db = ECN("db", "distanceBetween{}_and_{}".format(pointA, pointB))
	cmds.connectAttr(pointAttrA, db+".point1")
	cmds.connectAttr(pointAttrB, db+".point2")
	return db

def liveAimFromTo(pointFrom, pointTo):
	aim = ECN("aim", "aimFromTo")
	cmds.connectAttr(pointFrom, aim+".constraintTranslate")
	cmds.connectAttr(pointTo, aim+".target[0].targetTranslate")
	return aim

def driveShapeWithPivot(shape, tf=None):
	# i forsee a time of applying deformation layers
	# to controls themselves

	if not tf:
		tf = cmds.listRelatives(shape, parent=True)[0]

	if cmds.listConnections(tf+".rotatePivot", type="composeMatrix"):
		tfMat = cmds.listConnections(tf+".rotatePivot", type="composeMatrix")[0]
	else:
		tfMat = ECN("composeMat", "shapeTf_mat")
		con(tf+".rotatePivot", tfMat+".inputTranslate")

	geoTf = cmds.createNode("transformGeometry")
	initShape = edRig.node.duplicateShape(shape, search="Shape", replace="initShape")
	con(tfMat+".outputMatrix", geoTf+".transform")
	# polygon discrimination
	con(initShape+".local", geoTf+".inputGeometry")
	con(geoTf+".outputGeometry", shape+".create")
	cmds.setAttr(initShape+".visibility", 0)

def buildTangentMatrix(positionPlug, tangentPlug, upPlug):
	""" builds tangent matrix through basic double-cross method
	use for curves, meshes, surfaces etc """
	binormal = ECA("vectorProduct", n="binormal")
	normal = ECA("vectorProduct", n="normal")
	attr.conOrSet(tangentPlug, binormal + ".input1")
	attr.conOrSet(upPlug, binormal + ".input2")
	attr.conOrSet(tangentPlug, normal + ".input1")
	binormal.con("output", normal + ".input2")
	for i in [binormal, normal]:
		i.set("operation", 2)
		i.set("normalizeOutput", 1)
	matPlug = fourByFourFromCompoundPlugs(
		tangentPlug, normal + ".output", binormal + ".output", positionPlug,
		name="tangentMat")
	return matPlug



def matrixConstraint(driver, driven, offset=True, translate=True, rotate=True,
					 scale=True, space="world"):
	"""i swear to god i had this before i went to framestore"""
	decomp = cmds.createNode("decomposeMatrix",
							 n="matConst_{}_{}_decomp".format(driver, driven))
	# mult = cmds.createNode("multMatrix",
	#                        n="matConst_{}_{}_mult".format(driver, driven))

	if offset:
		driverMat = WorldMMatrixFrom(driver)
		drivenMat = WorldMMatrixFrom(driven)
		offsetMat = drivenMat * driverMat.inverse()

	if space == "local":
		# S P E E E  E   E    E      E        D
		if offset:
			offsetMat = core.MMatrixFrom(driven) * core.MMatrixFrom(driver).inverse()


	if not offset and space == "world":
		"""basic world space rivet - slow but reliable"""
		cmds.connectAttr(driven+".parentInverseMatrix[0]", mult+".matrixIn[0]")
		cmds.connectAttr(driver+".worldMatrix[0]", mult+".matrixIn[1]")

	cmds.connectAttr(mult+".matrixSum", decomp+".inputMatrix")
	attrList = []
	if translate:
		attrList.append("translate")
	if rotate:
		attrList.append("rotate")
	if scale:
		attrList.append("scale")
	for ax in "XYZ":
		for n in attrList:
			decompAttr = n[0].upper()+n[0:]
			cmds.connectAttr(driver+".output"+decompAttr+ax,
			                 driven+"."+n+ax, f=True)
	return mult, decomp


def connectTransformAttrs(driver, driven, translate=True,
                          rotate=True, scale=True):
	attrList = []
	if translate:
		attrList.append("translate")
	if rotate:
		attrList.append("rotate")
	if scale:
		attrList.append("scale")
	for ax in "XYZ":
		for n in attrList:
			# direct connections because parallel evaluation is competently made
			cmds.connectAttr(driver+"."+n+ax, driven+"."+n+ax, f=True)

def getTransformAttrs(node, translate, rotate, scale):
	"""wrap below properly to avoid copying"""
	attrList = []
	if translate:
		attrList.append("translate")
	if rotate:
		attrList.append("rotate")
	if scale:
		attrList.append("scale")
	for ax in "XYZ":
		for n in attrList:
			pass
	pass

def zeroTransforms(node):
	cmds.makeIdentity(node, apply=False)
	return node

def unpackTRS(t, r, s):
	""" gets translate, rotate, scale as strings from booleans """
	attrs = {"translate" : t, "rotate" : r, "scale" : s}
	return [k for k, v in attrs.items() if k]

def decomposeMatrixPlug(plug, target=None, t=1, r=1, s=1, shear=0):
	"""basic atomic decomposition"""
	decomp = ECA("decomposeMatrix", "decomposeMat"+plug)
	cmds.connectAttr(plug, decomp+".inputMatrix")

	if target: # hopefully a dag
		target = AbsoluteNode(target)
		for i in unpackTRS(t, r, s):
			for n in "XYZ":
				cmds.connectAttr(decomp+".output"+i.capitalize()+n,
				                 target+"."+i+n, f=1)
	if shear:
		cmds.connectAttr(decomp + ".outputShearX", target + ".shearXY")
		cmds.connectAttr(decomp + ".outputShearY", target + ".shearXZ")
		cmds.connectAttr(decomp + ".outputShearZ", target + ".shearYZ")
	return decomp

def multMatrixPlugs(plugs, name="matMult"):
	"""multiplies matrix plugs in given sequence"""
	node = ECA("multMatrix", n=name)
	for i, val in enumerate(plugs):
		cmds.connectAttr(val, node+".matrixIn[{}]".format(i))
	return node + ".matrixSum"

def aimToVector(transform, vector):
	aim = ECA("aimConstraint")
	aim.conOrSet(vector, aim+".target[0].targetTranslate")
	aim.con(aim+".constraintRotate", transform+".rotate")
	return aim

def getClosestPoint(target=(0,0,0), points=None):
	"""find closest point from selection of tuples"""
	lowest = 1000.0
	for i in points:
		vec = []
		for n in range(3):
			vec.append(target[n] - i[n])
		length = math.sqrt( pow(vec[0], 2) +
		                    pow(vec[1], 2) +
		                    pow(vec[2], 2) )
		if length < lowest:
			lowest = length


def unrollConstraint(constraint):
	""" remove or reroute the cyclic mess of connections
	that festoons each and every constraint node
	run last in rig building"""
	# used to look up driven transform
	historyAttr = "constraintRotateOrder"
	# attrs to reroute
	breakAttrs = ["constraintRotateOrder", "constraintRotatePivot",
	              "constraintRotateTranslate",]









