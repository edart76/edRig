# define all the pretty colours, and how to saving them
import edRig.core as core
from edRig.core import ECN, ECA, con, AbsoluteNode, invokeNode
from edRig import attr, transform, pipeline

import maya.cmds as cmds
import maya.api.OpenMaya as om

import string

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
			pipeline.safeImport(controlLibPath)
			# cmds.file( controlLibPath, i=True, type="mayaAscii",
			# 	defaultNamespace=True)
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


class FkControl(Control):
	# base for all controls whose physical location doesn't matter
	"""control dag structure is this: # contributes to output
	entry: organisation
		space grp:
			control grp:
				inverse grp: (only if control is marked as static
					ui controlA: # always last in output
						ui controlB : # only if necessary for offsets
					world output # separate world output, in same space
		localOutput: locator for use as point datatype
			"""

	types = ("curve", "surface")

	def __init__(self, name=None, layers=1, controlType="curve"):
		#super(FkControl, self).__init__(name)
		if not controlType in self.types:
			print "control type {} is invalid".format(controlType)
			controlType = "curve"
		self.controlType = controlType
		self.name = name
		self.spareInputs = {} # name, node
		self.layers = [None] * layers # absoluteNodes
		self.makeHierarchy()
		if layers:
			self.connectProxies()
			self.connectOutput()

	def makeHierarchy(self):
		"""creates uniform hierarchy, according to plan following class"""
		# main and local
		self.root = ECA("transform", name=self.name+"_control")
		self.localRoot = ECA("transform", name=self.name+"_localRoot")
		self.localOffset = ECA("transform",
		                       name=self.name+"_localOffset", parent=self.localRoot)
		#print "local offset " + self.localOffset
		self.localOutput = ECA("locator",
		                       name=self.name+"_localOutput", parent=self.localOffset)

		# ui and world
		self.uiRoot = ECA("transform",
		                       name=self.name+"_uiRoot", parent=self.root)
		# self.uiFollow = ECA("transform",
		#                        name=self.name+"_uiFollow", parent=self.uiRoot)
		self.uiOffset = ECA("transform",
		                       name=self.name+"_uiOffset", parent=self.uiRoot)

		transform.connectTransformAttrs(self.uiOffset, self.localOffset)

		# layers
		for i, val in enumerate(self.layers):
			letter = string.ascii_uppercase[i]
			if i != 0:
				controlName = self.name + "_" + letter
			else:
				controlName = self.name
			parent = self.uiOffset if i == 0 else self.layers[i-1]
			print "outer parent {}".format(parent)
			self.layers[i] = self.makeUiElement(name=controlName,
			                parent=parent)

			attr.makeStringConnection(self.uiRoot, self.layers[i],
			                          startName="ui"+letter,
			                          endName="uiRoot")

		self.worldOutput = ECA("locator",
		                        name=self.name+"_worldOutput",
		                        parent=self.uiOffset)
		self.worldOutput.hide()
		self.localOutput.hide()

		print "ctrl parent is {}".format(self.first.parent)

	def connectProxies(self):
		"""connect up proxy attributes from ui to local components
		if proxies don't work, move to more advanced ways like blendDevices
		and managing keys directly"""

		"""imperative to do more here, this is just a stopgap until a callback system
		is worked out
		there will be no parallelism with this yet"""

		pass

	def connectOutput(self):
		"""multiply local matrices and decompose to output
		keeping it uniform with matrix decomp even if unnecessary - if we ever
		get to the point of this being a bottleneck, we're doing alright"""
		plugs = [i + ".matrix" for i in self.layers]
		layerMult = transform.multMatrixPlugs(plugs,
		                                      name=self.name+"_layerMult")
		transform.decomposeMatrixPlug(layerMult, self.worldOutput)
		transform.connectTransformAttrs(self.worldOutput, self.localOutput)

	def makeUiElement(self, name="test", parent=None):
		"""make a proper visual representation at origin"""
		# for now just a circle
		ctrl = self.makeShape(name)
		print "ctrl {}".format(ctrl)
		print "parent {}".format(parent)
		if parent:
			cmds.parent(ctrl, parent)
		return ctrl

	def makeShape(self, name):
		"""makes either a circle or circular surface"""
		ctrl = cmds.circle(name="temp")[0]
		if self.controlType == "surface":
			surfaceTemp = cmds.planarSrf(ctrl)
			# returns transform, planarTrim node
			newTemp = cmds.duplicate(surfaceTemp[0], n="newCtrlTemp")[0]
			cmds.delete(ctrl, surfaceTemp[0], surfaceTemp[1])
			ctrl = cmds.rename(newTemp, name)
		else:
			ctrl = cmds.rename(ctrl, name)
		return AbsoluteNode(ctrl)

	def markAsGuides(self):
		"""turns everything bright yellow"""
		pass


	@property
	def outputPlug(self):
		"""returns the local matrix plug of control """
		return self.localOutput+".matrix"

	@property
	def worldOutputPlug(self):
		"""world output of the control (strongly not recommended for use)"""
		return self.worldOutput+".worldMatrix[0]"

	@property
	def shapes(self):
		"""returns list of ui shapes"""
		return [i.shape for i in self.layers]
	@property
	def first(self):
		"""returns first layer"""
		return self.layers[0]

"""new approach - uniform ctrl grp hierarchy:

ctrlName_controlRoot
| - ctrlName_localOffset
|   | - ctrlName_localOutput
|
| - ctrlName_uiRoot         | passes message attribute as marker back to follow group
    # | - ctrlName_uiFollow       | constrained to whatever
        | - ctrlName_uiOffset       | static offset group, same as local
            | - ctrlName_A              | visible ui controls
                | - ctrlName_B          |
                    | - ctrlName_C      |
                        | - ctrlName_worldOutput
by this system, concatenated controls sharing the same driver may still keep
separate offsets
"""



"""there is a difficulty in the controls - we only care about the translate, rotate
and scale attributes, directly input by the user; the user only cares about the visual
representation of the control, which should follow along with the full result of the rig,
not just its own values. the real component must be injected at the start of evaluation,
while the visual component need only follow along with the end.

contemplated proxy stuff to avoid backwards flow - HOPEFULLY that won't be necessary.
for now literally connect transform attributes from visual to real

of course because maya is amazing, even local transforms are not computed until
the object's world position is known.
woooooooooooooooooooooooo


"""
