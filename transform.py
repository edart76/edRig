# move stuff around
from edRig import core
from core import ECN, con, AbsoluteNode, ECA
import maya.cmds as cmds
import maya.api.OpenMaya as om

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

def matrixFromValues(vals):
	"""return an MMatrix from sequence of floats"""
	if not (len(vals) == 16 or len(vals) == 4):
		raise RuntimeError("wrong number of values supplied to matrix")
	return om.MMatrix(vals)

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
	rank = 4
	mat = ECA("fourByFourMatrix", name=name)
	for i in range(rank): # rows
		for n in range(rank): # columns
			index = i * 4 + n
			cmds.setAttr(mat+".in{}{}".format(i, n), vals[index])
	return mat+".output" if plug else mat

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

def matchTranformation(targetNode, followerNode, translation=True, rotation=True):
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
	initShape = core.duplicateShape(shape, search="Shape", replace="initShape")
	con(tfMat+".outputMatrix", geoTf+".transform")
	# polygon discrimination
	con(initShape+".local", geoTf+".inputGeometry")
	con(geoTf+".outputGeometry", shape+".create")
	cmds.setAttr(initShape+".visibility", 0)


def matrixConstraint(driver, driven, offset=True, translate=True, rotate=True,
					 scale=True, space="world"):
	"""i swear to god i had this before i went to framestore"""
	decomp = cmds.createNode("decomposeMatrix",
							 n="matConst_{}_{}_decomp".format(driver, driven))
	mult = cmds.createNode("multMatrix",
	                       n="matConst_{}_{}_mult".format(driver, driven))

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

def decomposeMatrixPlug(plug, target=None):
	"""basic atomic decomposition"""
	print "plug is {}".format(plug)
	decomp = ECA("decomposeMatrix", "decomposeMat"+plug)
	cmds.connectAttr(plug, decomp+".inputMatrix")

	if target: # hopefully a dag
		target = AbsoluteNode(target)
		for i in ["translate", "rotate", "scale"]:
			for n in "XYZ":
				cmds.connectAttr(decomp+".output"+i.capitalize()+n,
				                 target+"."+i+n)
	return decomp






