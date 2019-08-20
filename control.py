# define all the pretty colours, and how to saving them
from edRig import CURRENT_PATH
from edRig.core import ECN, con
from edRig.node import AbsoluteNode, ECA, invokeNode
from edRig import attr, transform, pipeline, material, beauty, plug

import maya.cmds as cmds
import maya.api.OpenMaya as om

import string

#controlLibPath = r'F:\\all projects desktop\common\edCode\edRig\data\ctrls\ctrlLibraryv02.ma'
controlLibPath = CURRENT_PATH + r'\data\ctrls\ctrlLibraryv02.ma'

validTypes = ["tet", "sphere", "dodec"]

class OldControl(object):
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
			pipeline.safeMayaImport(controlLibPath)
			# cmds.file( controlLibPath, i=True, type="mayaAscii",
			# 	defaultNamespace=True)
			libGrp = cmds.ls("*ctrlLib_grp")[0]
			cmds.setAttr(libGrp+".visibility", 0)

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


class Control(object):
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

	indexColours = ["none", "black"]

	types = ("curve", "surface")

	def __init__(self, name=None, layers=1, controlType="curve",
	             colour=(0,120,256) ):
		if not controlType in self.types:
			print "control type {} is invalid".format(controlType)
			controlType = "curve"
		self.controlType = controlType
		self.name = name
		self.spareInputs = {} # name, node
		self.layers = [None] * layers # absoluteNodes
		self.colour = beauty.getColour(colour)
		self.makeHierarchy()
		if layers:
			self.connectProxies()
			self.connectOutput()

		self.makeBeautiful(self.colour)

	def makeBeautiful(self, colour):
		"""pretty"""
		if self.controlType == "surface":
			controlMat = material.getUiShader(colour)
		for i in self.layers:
			beauty.setColour(i, colour)
			if self.controlType == "surface":
				try:
					controlMat.applyTo(i)
				except:
					pass


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

	def makeStatic(self):
		"""insert inverse offset group just above control
		not used in base class"""

		staticTf = ECA("transform", n=self.name+"_static")
		#staticTf.parentTo(self.first.parent, r=True)
		transform.decomposeMatrixPlug( self.first+".inverseMatrix",
		                               staticTf)
		self.first.parentTo(staticTf)
		return staticTf

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
		"""returns first layer
		:return AbsoluteNode"""
		return self.layers[0]

class ParametricControl(Control):
	"""controls sliding on curves or surfaces"""

	def __init__(self, name=None, layers=1,
	             controlType="sphere", colour=(0,0,1),
	             domainShape=None, auxShapeA=None, auxShapeB=None,
	             parametreScale=(10.0, 10.0, 10.0),
	             ):
		"""domainShape is shape on which control moves
		auxShapes may be used in certain curve configurations"""
		super(ParametricControl, self).__init__(name, layers,
		                                        controlType, colour)
		self.domainShape = domainShape
		self.parametreScale = parametreScale

	def makeHierarchy(self):
		"""we assume the same transform as the domain shapes
		shapeTf
			|- shape
			|- ctrl static grp
				|- ctrl"""
		ui = self.makeShape(self.name)
		self.layers[0] = ui
		static = self.makeStatic()


		mult = ECA("multMatrix", n=self.name+"_mult")
		ui.con(ui+".inverseMatrix", mult+".matrixIn[0]")


		shapemat = self.getShapeMatrix()
		mult.con(shapemat, mult+".matrixIn[1]")
		transform.decomposeMatrixPlug(mult+".matrixSum", static)

	def getShapeMatrix(self):
		""""""

	def makeStatic(self):
		"""remove complex operations"""
		static = ECA("transform", n=self.name+"_static")
		static.parentTo(self.domainShape.transform)
		self.first.parentTo(static)
		return static









class FkControl(Control):
	"""shell for inheriting main control"""

class TileControl(Control):
	"""literally just a square
	use to hold attributes,
	under no circumstances for driving motion directly"""
	
	def __init__(self, name, colour=(56, 120, 256) ):
		super(TileControl, self).__init__(name=name, layers=1,
		                                  controlType="surface",
		                                  colour=colour)

	def makeSquare(self, name=None):
		""""""
		name = name or self.name
		return AbsoluteNode(cmds.polyPlane(n=name, ch=False, sx=1, sy=0)[0])

	def makeHierarchy(self):
		"""make a square and make a group"""
		self.root = ECA("transform", name=self.name+"_control")
		self.square = self.makeSquare()
		self.square.parentTo(self.root)
		self.layers[0] = self.square
		self.worldOutput = self.square

	def connectOutput(self):
		pass







	"""include methods for adding tile to group of other tiles
	this may result in unpredictable arrangements, which is nice"""



class RampControl(Control):
	"""live ramp control in the scene connected to remapvalue network
	probably the most disco thing I've done at framestore"""
	pass

class ProximityControl(Control):
	"""for making a network of physically-linked positions
	representing values and interpolating between them"""

	def __init__(self, name="proximityCtrl", knots=None, numberOutputs=2):
		"""currently only a linear distance function is used
		:param knots : dict of {knotName : knotValue}
		currently only floats supported"""
		self.knots = knots or {"knot" : 1.0}
		self.knotCtrls = []
		for k, v in self.knots.iteritems():
			self.knotCtrls.append(self.makeSphere(name=k))

		self.outputs = [self.makeSphere() for i in range(numberOutputs)]

	def makeSphere(self, name=None):
		name = name or "sphere"
		return AbsoluteNode(cmds.sphere(n=name)[0])

	def makeHierarchy(self):
		self.root = self.uiRoot = ECA(
			"transform", name=self.name+"_domain")



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
