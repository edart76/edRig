# s o o n
import pprint
from maya import cmds, mel
import maya.api.OpenMaya as om
from edRig.core import AbsoluteNode, ECA
from edRig import curve, COMMON_PATH, pipeline, attr # lol

def exportShapeToTempFile(target):
	"""returns """
	cmds.select(clear=True)
	cmds.select(target)
	path = COMMON_PATH+"/temp/tempShapeExport.ma"
	return cmds.file(path, type="mayaAscii",
	                 exportSelectedStrict=True, f=True)

def getSurfaceInfo(shape):
	"""return info necessary to reconstruct surface
	:param shape : AbsoluteNode"""
	surfInfo = {}
	fn = shape.shapeFn
	tf = shape.transform

	# # needed for create
	surfInfo["cvs"] = [(i.x, i.y, i.z) for i in fn.cvPositions()]
	surfInfo["uKnots"] = [i for i in fn.knotsInU()]
	surfInfo["vKnots"] = [i for i in fn.knotsInV()]
	surfInfo["uDegree"] = fn.degreeInU
	surfInfo["vDegree"] = fn.degreeInV
	surfInfo["uForm"] = fn.formInU
	surfInfo["vForm"] = fn.formInV
	surfInfo["rational"] = True

	"""get mPlugs for .tf and .cached, then get and save setAttr cmds"""
	ccPlug = attr.getMPlug(shape+".cached")
	surfInfo["cached"] = str("".join(ccPlug.getSetAttrCmds()))

	tfPlug = attr.getMPlug(shape + ".tf")
	surfInfo["tf"] = str("".join(tfPlug.getSetAttrCmds()))

	#
	# # needed to keep trimmed shape
	# surfInfo["isTrimmedSurface"] = fn.isTrimmedSurface()
	# if surfInfo["isTrimmedSurface"]:
	# 	surfInfo["numRegions"] = fn.numRegions()
	# 	surfInfo["numBoundaries"] = fn.numBoundaries()
	# 	surfInfo["boundaryInfo"] = {}
	# 	for region in range(surfInfo["numRegions"]):
	# 		surfInfo["boundaryInfo"][region] = {}
	# 		for boundary in range(surfInfo["numBoundaries"]):
	# 			#surfInfo["boundaryInfo"][region][boundary] = {}
	# 			boundaryInfo = {
	# 				"boundaryType" : int(fn.boundaryType(region, boundary)),
	# 				"numEdges" : fn.numEdges(region, boundary),
	# 				"edgeInfo" : {},
	# 			}
	# 			for edge in range(boundaryInfo["numEdges"]):
	# 				# this is getting ridiculous
	# 				edgeFn = om.MFnNurbsCurve(fn.edge(
	# 					region, boundary, edge, False)) # returning 3d edge
	# 				edgeInfo = curve.getCurveInfo(fn=edgeFn)
	# 				boundaryInfo[edge] = edgeInfo
	#
	# 			surfInfo["boundaryInfo"][region][boundary] = boundaryInfo

	return surfInfo
	pass


def setSurfaceInfo(info, target=None, create=True, parent=None):
	"""apply info from dict, or just create anew"""
	fn = om.MFnNurbsSurface()
	target = AbsoluteNode(target).shape
	#return

	target.delete()
	targetName = target.name

	parent = AbsoluteNode(parent)

	print "info to set is {}".format(info)

	cvs = [om.MPoint(i) for i in info["cvs"]]
	shapeObj = fn.create(
		cvs,
		info["uKnots"],
		info["vKnots"],
		info["uDegree"],
		info["vDegree"],
		info["uForm"],
		info["vForm"],
		info["rational"],
		parent=parent.MObject,
	)
	fn.updateSurface()
	newShape = AbsoluteNode.fromMObject(shapeObj)
	print "newShape is " + newShape
	cmds.select(newShape, ne=True)
	for i in (info["cached"], info["tf"]):
		#cmd = str("".join(i).replace("\t", ""))
		#cmd = "".join(i)
		cmd = i
		#pprint.pprint(cmd)
		mel.eval(cmd)
	cmds.select(clear=True)

	# important to maintain wider references
	target.setMObject(shapeObj)
	target.name = targetName

	return shapeObj
	#return target


"""
create(cvs, uKnots, vKnots, uDegree, vDegree, uForm, vForm,
    rational, parent=kNullObj) -> MObject
    * cvs (MPointArray or seq of MPoint)
      - The control vertices.
* uKnots (MDoubleArray or seq of float)
      - Parameter values for the knots in the U direction.
* vKnots (MDoubleArray or seq of float)
      - Parameter values for the knots in the V direction.
* uDegree   (int) - Degree of the basis functions in the U direction.
* vDegree   (int) - Degree of the basis functions in the V direction.
* uForm     (int) - A Form constant (kOpen, kClosed, kPeriodic) giving
        the surface's form in the U direction.
* vForm     (int) - A Form constant (kOpen, kClosed, kPeriodic) giving
        the surface's form in the V direction.
* rational (bool) - Create as rational (True) or non-rational (False)
        surface.
"""

# needed for create
# surfInfo["cvs"] = [(i.x, i.y, i.z) for i in fn.cvPositions()]
# surfInfo["uKnots"] = fn.knotsInU()
# surfInfo["vKnots"] = fn.knotsInV()
# surfInfo["uDegree"] = fn.degreeInU
# surfInfo["vDegree"] = fn.degreeInV
# surfInfo["uForm"] = fn.formInU
# surfInfo["vForm"] = fn.formInV
# surfInfo["rational"] = True
#
# # needed to keep trimmed shape
# surfInfo["isTrimmedSurface"] = fn.isTrimmedSurface()
# if surfInfo["isTrimmedSurface"]:
# 	surfInfo["numRegions"] = fn.numRegions()
# 	surfInfo["numBoundaries"] = fn.numBoundaries()
# 	surfInfo["boundaryInfo"] = {}
# 	for region in range(surfInfo["numRegions"]):
# 		surfInfo["boundaryInfo"][region] = {}
# 		for boundary in range(surfInfo["numBoundaries"]):
# 			#surfInfo["boundaryInfo"][region][boundary] = {}
# 			boundaryInfo = {
# 				"boundaryType" : int(fn.boundaryType(region, boundary)),
# 				"numEdges" : fn.numEdges(region, boundary),
# 				"edgeInfo" : {},
# 			}
# 			for edge in range(boundaryInfo["numEdges"]):
# 				# this is getting ridiculous
# 				edgeFn = om.MFnNurbsCurve(fn.edge(
# 					region, boundary, edge, False)) # returning 3d edge
# 				edgeInfo = curve.getCurveInfo(fn=edgeFn)
# 				boundaryInfo[edge] = edgeInfo
#
# 			surfInfo["boundaryInfo"][region][boundary] = boundaryInfo
#
# 	# surfInfo["boundaryType"] = fn.boundaryType()