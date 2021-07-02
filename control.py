# define all the pretty colours, and how to saving them
from edRig import CURRENT_PATH
from edRig.maya.core import ECN
from edRig.maya.core.node import EdNode, ECA
from edRig import cmds, transform, pipeline, beauty, plug

import string

#controlLibPath = r'F:\\all projects desktop\common\edCode\edRig\data\ctrls\ctrlLibraryv02.ma'
controlLibPath = CURRENT_PATH + r'\data\ctrls\ctrlLibraryv02.ma'

validTypes = ["tet", "sphere", "dodec"]



class Control(object):
	"""no spaces, no layers for now
	use proxies to separate ui and output

	dag hierarchy is this:

	ctl grp
		- world position - placed by hand
            - world offsets - however many layers wanted
            first offset is reserved for matrix rivet
	            - world ui - layers
	                - world ui output
	    - static controls - transform layers mirroring ui, driven by proxies

	for parallel stuff each control needs a proxied transform at origin,
	but that is for later
	output specifies this local parallel copy,
	to be used for driving attributes
	worldOutput is the final ui output in worldspace, for parenting etc

			"""

	indexColours = ["none", "black"]

	types = ("curve", "surface")

	def __init__(self, name=None, uiLayers=1, offsetLayers=1,
	             controlType="curve",
	             colour=(0,120,256), build=True ):

		self.controlType = controlType
		self.name = name
		self.guide = None # template guide control

		self.uis = [None] * uiLayers # type: [EdNode]
		self.locals = [None] * uiLayers # type: EdNode
		self.offsets = [None] * max(1, offsetLayers) # type: list([EdNode])
		self.colour = colour

		self._output = None
		self._worldOutput = None

		if build:
			self.build()


	@property
	def worldOutput(self):
		return self.uis[-1]

	@property
	def output(self):
		""" change when parallel comes online """
		return self.locals[-1]

	def build(self):
		self.createHierarchy()
		#self.createConnections()

	def createHierarchy(self):
		"""creates one control and one offset group and that is it"""
		self.root = parent = ECA("transform", name=self.name+"_controlGrp")
		self.root.lock() # lock all root attributes, should remain at origin

		# create offset groups, to be moved around in scene
		# redo these as direct parentOffset connections
		for i in range(len(self.offsets)):
			self.offsets[i] = ECA("transform",
			    n=self.name + "_offset" + string.ascii_uppercase[i],
			                      parent=parent)
			parent = self.offsets[i]

		# create ui shapes
		localParent = self.root
		for i in range(len(self.uis)):
			if len(self.uis) == 1: # no point in letters
				name = self.name + "_ctl"
			# subcontrol naming convention: "C_spinex2" ?
			else: name = self.name + "x{}".format(i) + "_ctl"
			self.uis[i] = self.createShape(name, iteration=i)
			self.uis[i].parentTo(parent)
			parent = self.uis[i]

			# local counterpart, which will receive keys
			self.locals[i] = ECA("transform", n=name+"Local")
			self.locals[i].parentTo(localParent)
			self.locals[i].hide() # hidden nodes eval faster
			localParent = self.locals[i]
		"""using parenting for now, test later if flat hierarchy
		and adding / multiplying attributes is more efficient"""

		# single output node necessary for matrices to work properly
		self._output = ECA("transform", n=self.name+"LocalOutput",
		                   parent=self.root)



	def createConnections(self):
		""" for each ui layer, proxy each of its keyable attributes
		to its local counterpart
		relies on attributes being common across all transforms """
		for local, world in zip(self.locals, self.uis):
			for i in world.attrs(keyable=True):
				world.connectProxyPlug( local + "." + i, i)






	def connectOutput(self):
		"""multiply local matrices and decompose to output
		keeping it uniform with matrix decomp even if unnecessary - if we ever
		get to the point of this being a bottleneck, we're doing alright"""
		plugs = [i + ".matrix" for i in self.uis]
		layerMult = transform.multMatrixPlugs(plugs,
		                                      name=self.name+"_layerMult")
		transform.decomposeMatrixPlug(layerMult, self.worldOutput)
		#transform.connectTransformAttrs(self.worldOutput, self.localOutput)


	def createShape(self, name, iteration=0):
		"""makes either a circle or circular surface"""
		ctrl = cmds.circle(name="temp_ctl_")[0]
		colour = beauty.darker(self.colour, factor=iteration * 0.07)
		beauty.setColour(ctrl, colour)
		if self.controlType == "surface":
			surfaceTemp = cmds.planarSrf(ctrl)
			# returns transform, planarTrim node
			newTemp = cmds.duplicate(surfaceTemp[0], n="newCtrlTemp")[0]
			cmds.delete(ctrl, surfaceTemp[0], surfaceTemp[1])
			ctrl = cmds.rename(newTemp, name)
		else:
			ctrl = cmds.rename(ctrl, name)
		# shrink secondary controls
		for ax in "XYZ":
			cmds.setAttr(ctrl + ".scale" + ax, 1.0 - 0.1 * iteration)
		cmds.makeIdentity(ctrl, apply=True)
		return EdNode(ctrl)

	def showGuides(self):
		"""turns everything bright yellow"""
		pass

	def hideGuides(self):
		"""removes yellow """

	def makeStatic(self):
		"""insert inverse offset group just above control
		not used in base class"""

		staticTf = ECA("transform", n=self.name+"_staticGrp",
		               parent=self.offsets[-1])
		transform.decomposeMatrixPlug( self.first+".inverseMatrix",
		                               staticTf)
		self.uis[0].parentTo(staticTf)
		return staticTf

	@property
	def outputPlug(self):
		"""returns the local matrix plug of control """
		return self.output+".matrix"

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
		:return EdNode"""
		return self.layers[0]

	def memoryInfo(self):
		"""return dict formatted for op memory """
		return {
			self.name + "Shape" : {
				"infoType" : ["shape"],
				"nodes" : [i.shape for i in self.uis]
			},
			self.name + "Attrs" : {
				"infoType" : ["attr"],
				"nodes" : self.uis + [self.guide, self.root]
			},
			self.name + "Transforms": {
				"infoType" : ["xform"],
				"nodes" : self.offsets
			}
		}

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

	def createHierarchy(self):
		"""we assume the same transform as the domain shapes
		shapeTf
			|- shape
			|- ctrl static grp
				|- ctrl"""
		ui = self.createShape(self.name)
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



def makeDomainCtrlTemp(domainSurface, name="domainCtl"):

	offsetGrp = ECA("transform", name=name+"_valueOffset")
	ctl = EdNode(cmds.circle(name=name + "_CTL", ch=0)[0])
	jnt = ECA("joint", n=name + "_jnt", parent=ctl)
	slideGrp = ECA("transform", n=name+"_slide")
	staticGrp = ECA("transform", n=name+"_static", parent=slideGrp)
	ctl.parentTo(offsetGrp) # offset specifies starting position
	offsetGrp.parentTo(staticGrp)

	surface = EdNode(domainSurface).shape

	# scaling attribute
	ctl.addAttr(ln="valueScale", dv=0.3)

	# make control static
	localMat = plug.multMatrixPlugs([ctl + ".matrix", offsetGrp + ".matrix"])
	invMat = plug.invertMatrixPlug( localMat)
	transform.decomposeMatrixPlug(invMat, staticGrp)

	psi = ECA("pointOnSurfaceInfo", n=name+"_psi")
	surface.con(surface.outWorld, psi + ".inputSurface")

	uPlug = plug.multLinearPlugs(ctl + ".translateX", ctl + ".valueScale")
	uPlug = plug.addLinearPlugs(uPlug, offsetGrp + ".translateX")
	uPlug = plug.setPlugLimits(uPlug, 0.001, max=100)

	vPlug = plug.multLinearPlugs(ctl + ".translateY", ctl + ".valueScale")
	vPlug = plug.addLinearPlugs(vPlug, offsetGrp + ".translateY")
	vPlug = plug.setPlugLimits(vPlug, 0.001, max=100)

	psi.con(uPlug, "parameterU" )
	psi.con(vPlug, "parameterV" )

	orientMat = transform.fourByFourFromCompoundPlugs(
		psi + ".normalizedTangentU",
		psi + ".normalizedTangentV",
		psi + ".normalizedNormal",
		psi + ".position"
	)

	transform.decomposeMatrixPlug(orientMat, slideGrp)
	# works alright



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
		return EdNode(cmds.polyPlane(n=name, ch=False, sx=1, sy=0)[0])

	def createHierarchy(self):
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
		for k, v in self.knots.items():
			self.knotCtrls.append(self.makeSphere(name=k))

		self.outputs = [self.makeSphere() for i in range(numberOutputs)]

	def makeSphere(self, name=None):
		name = name or "sphere"
		return EdNode(cmds.sphere(n=name)[0])

	def createHierarchy(self):
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
