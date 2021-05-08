#useful tools and larger procedures
from . import core
from .core import ECN
from edRig import curve, transform, mesh, surface, attr, control, \
	cmds, om, plug, con
import time


def closestMatrixToMatrixPlug(fromPlug, closestPoint=None, upCurvePlug=None):
	""" type-agnostic function for constraining matrices with previous geo """
	plugType = attr.plugType(fromPlug)
	if plugType == "matrix":
		return fromPlug
	elif plugType == "nurbsCurve" or plugType == "bezierCurve":
		u = curve.getClosestU(fromPlug, closestPoint)
		mat = curve.liveMatrixAtU(fromPlug, u=u, constantU=True,
		                           purpose="getPoint", upCurve=upCurvePlug)["mat"]
		return mat+".output"
		#pciCtrl = control.TileControl()
	elif plugType == "mesh":
		data = mesh.closestPointOnMesh()



# rotate transform around axis vector with quaternion
def quatAxis(inSpace="", pos=[1,0,0], axis=[0,0,1],
	theta=0, offset=180, length=1, name="quatAxis", target=""):

	# rotate a point around a vector with the power of 4D maths
	# nodes
	n = core.nameDeco(name)

	thetaInput=ECN("adl", n+"thetaInput")
	lengthInput=ECN("adl", n+"lengthInput") # aka radius input

	thetaMult = ECN("mdl", n+"thetaMult")
	axisVmp = ECN("vp", n+"axisVmp", "vmp")
	posVmp = ECN("vp", n+"posVmp", "vmp")
	trigTheta = ECN("etq", n+"trigTheta")
	nSinTheta = ECN("md", n+"nSinTheta")

	posNorm = ECN("qtn", n+"posNorm")
	axisNorm = ECN("qtn", n+"axisNorm")

	qPosProd = ECN("qtp", n+"qPosProd")
	qConj = ECN("qtc", n+"qConj")
	qPosConjProd = ECN("qtp", n+"qPosConjProd")

	lengthMult = ECN("md", n+"lengthMult")

	#build
	con(thetaInput+".output", thetaMult+".input1")
	core.edSet(thetaMult+".input2", 2)
	con(thetaMult+".output", trigTheta+".inputRotateX")
	con(trigTheta+".outputQuatX", nSinTheta+".input1")
	con(axisVmp+".output", nSinTheta+".input2")
	con(axisVmp+".matrix", posVmp+".matrix")
	con(nSinTheta+".output", axisNorm+".inputQuat")
	con(trigTheta+".outputQuatW", axisNorm+".inputQuatW")

	con(posVmp+".output", posNorm+".inputQuat")

	con(axisNorm+".outputQuat", qPosProd+".input1Quat")
	con(axisNorm+".outputQuat", qConj+".inputQuat")
	con(posNorm+".outputQuat", qPosProd+".input2Quat")

	con(qPosProd+".outputQuat", qPosConjProd+".input1Quat")
	con(qConj+".outputQuat", qPosConjProd+".input2Quat")

	con(lengthInput+".output", lengthMult+".input1")
	con(qPosProd+".outputQuat", lengthMult+".input2")

	#io
	inputs = [
	axisVmp+".matrix", posVmp+".input1", axisVmp+".input1",
	thetaInput+".input1", thetaInput+".input2", lengthInput+".input1"
	]

	testArgs = [inSpace, pos, axis, theta, offset, length]
	for i, val in enumerate(testArgs):
		#print "i is {}, val is {}".format(i, val)
		if core.isAttr(val):
			con(val, inputs[i])
		else:
			core.edSet(inputs[i], val)
	if target:
		con(lengthMult+".output", target)

	return thetaInput, lengthInput
	#my tools are the best
	print("ey")

# get vector from start to end
def vecFromTo(start, end):
	#get vector from start plug to end
	# add checking like on pciAtU
	startN = (core.nodeFromAttr(start)).capitalize()
	endN = (core.nodeFromAttr(end)).capitalize()

	# make it work with transforms:
	transformList = []
	for i in (start, end):
		if not core.isAttr(i):
			#print "i is {}".format(i)
			if core.isType(i, "transform"):
				print("yup")
				i = i+".translate"
		transformList.append(i)

	vec = ECN("pma",
		"vec{}to{}".format(startN, endN),
		"-")

	in1 = vec + ".input3D[0]"
	in2 = vec + ".input3D[1]"
	out = vec + ".output3D"
	con(transformList[0], in1)
	con(transformList[1], in2)
	return out

# rip carpal forever
def planeIntersect(vecBase, vecEnd, plane, planeNormal=[1,0,0],
	target="", name="planeIntersect"):
	# YEAAAAAAAAA BOI
	# carpal's elbows finally defeated

	n = core.nameDeco(name)
	transformList = []
	for i in (vecBase, vecEnd, target):
		if not core.isAttr(i):
			#print "i is {}".format(i)
			if core.isType(i, "transform"):
				print("yup")
				i = i+".translate"
		transformList.append(i)
	vecBase, vecEnd, target = transformList

	pN = ECN("vp", n+"planeNormal", "vmp")
	OminusA = vecFromTo(plane, vecBase)
	OminusAtimesN = ECN("md", n+"OminusAtimesN")
	intersectVec = vecFromTo(vecBase, vecEnd)
	DtimesN = ECN("md", n+"DtimesN")
	neg = ECN("md", n+"negative")
	lowerCombine = ECN("pma", n+"lowerCombine")
	upperCombine = ECN("pma", n+"upperCombine")
	overResult = ECN("md", n+"overResult", "div")
	tMult = ECN("md", n+"tMult")
	intersectPlusTval = ECN("pma", n+"sectPlusTval")

	#build
	con(plane+".matrix", pN+".matrix")
	core.edSet(pN+".input1", planeNormal)
	con(pN+".output", DtimesN+".input1")
	con(pN+".output", OminusAtimesN+".input1")
	con(OminusA, OminusAtimesN+".input2")
	con(OminusAtimesN+".output", upperCombine+".input1D")
	con(upperCombine+".output1D", overResult+".input1X")

	con(intersectVec, DtimesN+".input2")
	con(DtimesN+".output", neg+".input1")
	#core.edSet(neg+".input2", -1)
	core.edSet(neg+".input2", 1) # screw it
	con(neg+".output", lowerCombine+".input1D")
	con(lowerCombine+".output1D", overResult+".input2X")

	con(overResult+".outputX", tMult+".input1")
	con(intersectVec, tMult+".input2")
	con(vecBase, intersectPlusTval+".input3D[0]")
	con(tMult+".output", intersectPlusTval+".input3D[1]")
	if target:
		con(intersectPlusTval+".output3D", target)

	return intersectPlusTval+".output3D"
	# fucking destroyed

# interpolate between arbitrary live values with a remap and nurbs curve
# live version - pass a list of attribute connections
def interpolateLive(lookup, values, inMin=0, inMax=1,
		name="interpolate", interp="linear", output="", swag=True):
	# use a remapValue to lerp between data
	# must be single linear attributes

	if swag:
		boundCrv = curve.curveFromCvs(values, deg=1,
			mode="live1d", name=name+"_techCrv")
			# this curve isn't actually needed, but i like it anyway
			# doesn't do anything, just looks cool
	rmv = ECN("rmv", name+"rmv")
	step = 1.0/len(values)

	core.debug(step)

	con(lookup, rmv+".inputValue")
	if output:
		con(rmv+".outValue", output)

	if interp == "linear":
		interp = 0
	elif interp == "smooth":
		interp = 1
	elif interp == "spline":
		interp = 2 # i suck

	#con(boundCrv+".boundingBoxMaxY", rmv+".outputMax")
	#con(boundCrv+".boundingBoxMinY", rmv+".outputMin")
	#core.edSet(rmv+".inputMin", inMin)
	#core.edSet(rmv+".inputMax", inMax)
	# totally useless. this node is so weird

	for i in range(len(values)):

		cmds.connectAttr(values[i], "{}.value[{}].value_FloatValue".format(rmv, i))
		pos = step * i
		core.debug(pos)

		#force it
		cmds.connectAttr(values[i], "{}.value[{}].value_Position".format(rmv, i))
		cmds.disconnectAttr(values[i], "{}.value[{}].value_Position".format(rmv, i))

		cmds.setAttr("{}.value[{}].value_Position".format(rmv, i), step*i)

		cmds.setAttr("{}.value[{}].value_Interp".format(rmv, i), interp)

		#cPoint = cmds.getAttr("{}.controlPoints[{}].yValue".format(boundCrv, i))
		# core.isType(values[i], "transform")
		# core.argLink(values[i], cPoint, attr)
		#if core.isAttr(values[i]):
			#con(values[i]+attr, cPoint)

		# don't think about it
	return rmv

# save any attribute and reset it
def saveReset(ctrl, name="memory", targetAttr="", display=True):
	# add enum to save and reset value, usually as a switch for blocking
	# move this to an attribute lib if I ever need one

	check = ECN("cnd", name+"_saveCheck")
	save = ECN("adl", name+"_save")
	refresh = ECN("pb", name+"_refresh")
	constant = ECN("adl", name+"_refreshConstant")
	input = ECN("adl", name+"_saveInput")

	# check out this one weird trick
	cmds.addAttr(ctrl, ln=name+"Save", at="enum", en="saved:reset", k=True)
	con(ctrl+"."+name+"Save", check+".firstTerm")
	core.edSet(check+".colorIfTrueR", 2)
	core.edSet(check+".colorIfFalseR", 0)

	if display:
		cmds.addAttr(ctrl, ln=name, k=True)
		con(save+".output", ctrl+"."+name)

	con(input+".output", save+".input1")
	con(input+".output", refresh+".inTranslateX2") # i want to vomit
	con(constant+".output", refresh+".inTranslateX1") # i want to die
	con(refresh+".outTranslateX", ctrl+"."+name+"Save")
	cmds.setAttr(refresh+".weight", 0)
	# with this system, the instant the input updates it will block
	# ideally it would block the second the node itself updates, but oh well
	if targetAttr:
		con(targetAttr, input+".input1")

	#only actually block at the end of build, allows attribute
	#to be registered immediately
	con(check+".outColorR", save+".nodeState")
	cmds.setAttr(ctrl+"."+name+"Save", 1)
	#time.sleep(1) # wtf
	# look into forcing evaluation at this point
	# openmaya will be involved
	cmds.setAttr(ctrl+"."+name+"Save", 0)

	returnDict = {}
	returnDict["input"] = input+".input1"
	returnDict["output"] = {}
	returnDict["output"]["blocking"] = check+".outColorR"
	returnDict["output"]["val"] = save+".output"
	return returnDict

# segmented plates are not evil
def sequentialLimits(attr, increment=1.0, steps=5, compound=False, n=""):
	# only with linear attributes for now - improve as needed
	# also compound is in general better practice than sequential for plates

	pr = "seqLimit"
	input = ECN("adl", n+pr+"input")
	outList = []
	subs = []
	clamps = []
	for i in range(steps):
		clamp = ECN("clamp", "{}{}{}limit".format(n, pr, i))
		clamps.append(clamp)
		if i == 0:
			core.debug(input)
			core.debug(clamp)
			con(input+".output", clamp+".inputR")
			core.edSet(clamp+".maxR", increment)
			con(attr, input+".input1")
		else:
			if not compound:
				con(clamps[i-1]+".maxR", clamp+".maxR")
				sub = ECN("pma", "{}{}{}limitSub".format(n, pr, i), "-")
				subs.append(sub)
				cmds.connectAttr(input+".output", sub+".input1D[0]")
				cmds.connectAttr(clamps[i-1]+".maxR", sub+".input1D[1]")
				con(sub+".output1D", clamp+".inputR")

			else:
				limitMult = ECN("mdl", n+pr+"limitMult")
				con(clamps[0]+".maxR", limitMult+".input1")
				core.edSet(limitMult+".input2", i+1)
				con(limitMult+".output", clamp+".maxR")
				con(input+".output", clamp+".inputR")

		outList.append(clamp+".outputR")
	return outList
