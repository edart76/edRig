
"""
it would be better for integration to have a c++
"drawing" context to let you drag out strokes in the viewport,
then set the coords of those strokes on to node attributes or
nurbs curves or something

when affecting chain, use the average plane and position of the existing chain
to project the stroke from camera

"""



import maya.cmds as cmds

import maya.api.OpenMaya as om
import maya.api.OpenMayaUI as omui2

draggerContextName = "myDragger"


def viewToWorld(screenX, screenY):
	worldPos = om.MPoint()  # out variable
	worldDir = om.MVector()  # out variable

	activeView = omui2.M3dView().active3dView()
	activeView.viewToWorld(int(screenX), int(screenY), worldPos, worldDir)

	return worldPos, worldDir


def getCameraWorldViewDirection():
	activeView = omui2.M3dView().active3dView()
	cameraPath = activeView.getCamera()
	fnCamera = om.MFnCamera(cameraPath)
	return fnCamera.viewDirection(om.MSpace.kWorld)


def doIntersect(pos):
	# Raysource rs, Raydirection rd
	rs = pos[0]
	rd = pos[1]

	print(("Ray source:", rs[0], rs[1], rs[2]))
	print(("Ray direction:", rd[0], rd[1], rd[2]))

	# position should be transform of selected object, if nothing selected it is 0 0 0, otherwise it should be selected dag object's world position to create object plane. I'll just implement view plane here
	position = om.MPoint(0, 0, 0)

	# View direction in world space is our plane's normal vector
	nPlane = getCameraWorldViewDirection()
	dl = rd * nPlane

	# Ray is on the plane or parallel to the plane, shouldn't be possible
	if dl == 0:

		dl = (position - rs) * nPlane
		if dl == 0:
			print()
			"On the plane"
		else:
			print()
			"Parallel"
	else:
		d = (position - rs) * nPlane / dl
		point = rs + d * rd
		print(("Intersect with view plane at:", point[0], point[1], point[2]))


def dragger_onPress():
	pos = cmds.draggerContext(draggerContextName, query=True, anchorPoint=True)
	print(("pos", pos[0], pos[1]))
	pos = viewToWorld(pos[0], pos[1])
	doIntersect(pos)


def dragger_onDrag():
	pos = cmds.draggerContext(draggerContextName, query=True, dragPoint=True)
	print(("pos", pos[0], pos[1]))
	pos = viewToWorld(pos[0], pos[1])  # get the first value of the tuple
	doIntersect(pos)


if (cmds.contextInfo(draggerContextName, exists=True)):
	cmds.deleteUI(draggerContextName, toolContext=True)

cmds.draggerContext(draggerContextName, pressCommand=dragger_onPress, dragCommand=dragger_onDrag, cursor="crossHair")
cmds.setToolTo(draggerContextName)
