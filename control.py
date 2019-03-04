# define all the pretty colours, and how to saving them
import edRig.core as core
from edRig.core import ECN, ECA, con, AbsoluteNode, invokeNode
from edRig import attr, transform

import attrio
import curve

import maya.cmds as cmds
import maya.api.OpenMaya as om

controlLibPath = r'F:\\all projects desktop\common\edCode\edRig\data\ctrls\ctrlLibraryv02.ma'

class Control(object):
	#base class for all forms of control
	def __init__(self, name, type="tet"):
		self.name = name
		self.tf = None
		self.shape = None

		if type:
			self.createControl(type)

	def createControl(self, type):
		# has the library already been imported?
		libGrp = cmds.ls("*ctrlLib_grp")
		if not libGrp:
			cmds.file( controlLibPath, i=True, type="mayaAscii",
				defaultNamespace=True)
			libGrp = cmds.ls("*ctrlLib_grp")[0]
			cmds.setAttr(libGrp+".visibility", 0)
		validTypes = ["tet", "sphere", "dodec"]
		newCtrl = cmds.duplicate(type+"_base", name=self.name+"_ctrl", rc=True)
		self.tf = cmds.parent(newCtrl[0], w=True)[0]
		self.shapes = cmds.listRelatives(newCtrl[0], shapes=True)
		# controls may have many shapes for beauty reasons
		# add something here to apply saved deformations once data folder
		# is properly set up
		self.pivotLoc = [x for x in cmds.listRelatives(self.tf,
			shapes=False, children=True) if "pivot" in x][0]
		self.pivotLoc = cmds.rename(self.pivotLoc, self.name+"_pivot")
		cmds.connectAttr(self.tf+".rotatePivot", self.pivotLoc+".translate")

		# handy to have
		self.world = self.pivotLoc+".worldMatrix[0]"
		self.worldD = ECN("matDecomp", self.name+"_worldSpaceDecomp")
		cmds.connectAttr(self.world, self.worldD+".inputMatrix")
		self.worldTrans = self.worldD + ".outputTranslate"
		self.worldRot = self.worldD + ".outputRotate"


	def pinShapesToPivot(self, shapes="all"):
		if shapes=="all":
			shapeList = self.shapes
		else:
			shapeList = [x for x in shapes if x in self.shapes]
		for i in shapeList:
			transform.driveShapeWithPivot(i)

	def reparentUnder(self, parent):
		# seriously fuck maya
		self.tf = cmds.parent(self.tf, parent)[0]


	# add property to rename control and children when self.name changes
	# @property
	# def name(self, value):
	#     self.tf = cmds.rename(self.tf, name+"_ctrl")
	#     # for i in cmds.listRelatives(self.tf, children=True, recursive=True):
	#     self.name = value

# class ControlTransform(object):
#     # simple wrapper around dag objects, mainly to make tf class attributes
#     # robust to hierarchy changes
#     def __init__(self, transform):
#         # would be very nice to return the string of the transform
#         self.tf = transform
	# def reparentUnder(self, parent):
	#     # seriously fuck maya
	#     self.tf = cmds.parent(self.tf, parent)[0]


class FkControl(Control):
	# base for all controls whose physical location doesn't matter
	"""control dag structure is this: # contributes to output
	entry: organisation
		spareWorldInputA # first in output
		space grp:
			control grp:
				inverse grp: (only if control is marked as static
					ui control: # always last in output
						world output # separate world output
			spareControlInputA # mid in output
			"""

	def __init__(self, name):
		super(FkControl, self).__init__(name)
		self.tf = None
		self.shape = None
		self.spareInputs = {} # name, node
		self.combineNode = None

	@property
	def output(self):
		"""returns the local matrix plug of control unless there are spare inputs,
		in which case it refreshes them and reconnects them"""
		if not self.spareInputs:
			return self.tf+".matrix"
		else:
			return self.matrixCombination+".matrixSum"

	@property
	def matrixCombination(self):
		if not self.combineNode:
			self.combineNode = ECA("multMatrix", self.name+"_matrixCombination")
		if not self.spareInputs:
			return self.combineNode
		self.updateCombination()
		return self.combineNode

	def updateCombination(self):
		"""update and reconnect spare inputs"""
		attr.breakConnections(self.combineNode, source=True)
		for i, val in enumerate(self.spareInputs.values()):
			cmds.connectAttr(val + ".matrix", self.combineNode + ".matrixIn[{}]".format(i))
		cmds.connectAttr(self.ui + ".matrix", self.combineNode + ".matrixIn[{}]".format(i + 1))

	def makeUi(self):
		"""creates ui shape, parents it to control group (which should by now
		be at home position and zeroes transforms"""
		temp = cmds.circle(n=self.name, ch=False, normal=(1,0,0), r=3)
		tf = AbsoluteNode(temp[0])
		shape = AbsoluteNode(cmds.listRelatives(tf, shapes=True))
		self.tf = tf
		self.shape = shape
		cmds.parent(self.tf, self.controlGrp)
		transform.zeroTransforms(self.tf)

	@property
	def ui(self):
		return self.tf

	@property
	def entry(self):
		"""first top level group of control, placed at origin"""
		return invokeNode(name=self.name+"_entry", type="transform")

	@property
	def spaceGrp(self):
		"""group used to drive the space of a control"""
		return invokeNode(name=self.name + "_space", type="transform",
		                  parent=self.entry)

	@property
	def controlGrp(self):
		"""container around control for safety"""
		return invokeNode(name=self.name + "_controlGrp", type="transform",
		                  parent=self.spaceGrp)

	@property
	def worldOutput(self):
		"""world output of the control (strongly not recommended for use)"""
		marker = invokeNode(name=self.name + "_controlGrp", type="locator",
		                  parent=self.spaceGrp)
		transform.zeroTransforms(marker)
		return marker



"""there is a difficuly in the controls - we only care about the translate, rotate
and scale attributes, directly input by the user; the user only cares about the visual
representation of the control, which should follow along with the full result of the rig,
not just its own values. the real component must be injected at the start of evaluation,
while the visual component need only follow along with the end.

contemplated proxy stuff to avoid backwards flow - HOPEFULLY that won't be necessary.
for now literally connect transform attributes from visual to real
"""
