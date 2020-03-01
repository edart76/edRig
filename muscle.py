from edRig import AbsoluteNode, ECA, curve, beauty, attr, \
	control, plug, transform
from edRig.dynamics import Nucleus, NHair, makeCurveDynamic
from edRig.scene import TidyManager, SceneObject


class Muscle(SceneObject):
	""" base class for muscle systems, involving more advanced
	interaction with dynamics """

	colours = {
		"muscle0" : (60, 30, 10), # deepest anchor muscle
		"muscle1" : (100, 60, 10), # intermediate muscles
		"muscle2" : (150, 100, 10) # top-level floating muscles
	}

	def __init__(self, name="newMuscle"):
		""" set name of muscle component """
		self.name = name

	@property
	def setupGrp(self):
		return self.invokeNode(self.name)

	@property
	def techGrp(self):
		return self.invokeNode(self.name+"_tech", parent=self.setupGrp)



class MuscleCurve(Muscle):
	"""dynamic curve making relative motions according to changes in length
	includes a bulge vector and ramp"""

	# solvers to transfer muscle deformation to mesh
	transferSolvers = ("joints", "wire")
	upSolvers = ("ctrlPos", "surfaceNormal")

	def __init__(self, hair, name="newMuscle",
	             collisionRigid=None,
	             jointRes=5,
	             upSolver=""):
		"""initialise with base hair system governing muscle behaviour
		:param NHair hair: """
		super(MuscleCurve, self).__init__(name)
		self.hair = hair
		self.jointRes = jointRes
		self.collider = collisionRigid
		self.ctrl = None

		# internal attributes
		self.joints = []
		self.rebuild = None

		self.muscleDepth = 0

	@property
	def muscleColour(self):
		key = "muscle" + str(self.muscleDepth)
		return self.colours[key]


	@classmethod
	def create(cls, baseCrv, nucleus=None,
	           jointRes=5,
	           upSolver="ctrlPos",
	           timeInput="time1.outTime",
	           name="testMuscle",
	           upSurface=None,
	           ):
		"""upSolver governs upvector for joints - """
		# insert live rebuild before dynamics
		newCurve, rebuild = cls.rebuildCurve(baseCrv, name=name+"_input")
		hair = makeCurveDynamic(newCurve, live=True, timeInput=timeInput,
		                 nucleus=nucleus, name=name)
		muscle = cls(hair, jointRes=jointRes,
		                     name=name, upSolver=upSolver)
		muscle.rebuild = rebuild # bit messy

		with TidyManager(muscle.setupGrp):
			muscle.makeControl()
			muscle.setup()
			muscle.joints = muscle.makeJoints()
		return muscle

	@classmethod
	def rebuildCurve(cls, baseCrv, name=""):
		rebuild = curve.rebuildCurve(baseCrv+".local", name+"Rebuild")
		newCrv = AbsoluteNode(baseCrv).shape.getShapeLayer(
			name=baseCrv+"_rebuilt")
		newCrv.con(rebuild + ".outputCurve", "create")
		return newCrv.transform, rebuild

	def setDepth(self, depth=0):
		""" sets depth of muscle, regarding how deeply it connects in body """
		self.muscleDepth = depth
		self.makeDisplay()

	def setLockedPoints(self, mode="none"):
		options = ["none", "start", "end", "both"]
		self.ctrl.first.set("pointLock", options.index(mode))


	# build methods --------

	def makeControl(self):
		"""create control attributes"""
		self.ctrl = control.TileControl(name=self.name,
		                                colour=(56, 120, 256) )
		node = AbsoluteNode(self.ctrl.first)
		#print "inputShape {}".format(self.hair.inputShape)
		baseTf = self.hair.inputShape.transform
		self.ctrl.root.parentTo(baseTf)

		crvDag = ECA("transform", self.name+"_ctrlRivet")
		curve.curveRivet(crvDag, self.hair.inputShape, 0.5)
		#transform.matchMatrix(crvDag, self.ctrl.first)
		transform.matchXforms(self.ctrl.root, crvDag)
		transform.zeroTransforms(self.ctrl.root)

		scale = beauty.getUsableScale(self.hair.outputLocalShape, factor=0.1)
		self.ctrl.first.set("scale", scale)
		self.ctrl.first.set("translateY", -scale)

		crvDag.delete()

		# set up muscle attributes
		# activation
		baseLength = curve.arcLength(self.hair.outputLocalShape)
		active = node.addAttr(attrName="activation", attrType="float", min=0, max=1, dv=0)
		length = node.addAttr(attrName="tensedLength", attrType="float",
		                      min=0, dv=baseLength / 3.0)
		restStretch = node.addAttr(attrName="restStretchResistance", attrType="float",
		                            min=1.0, dv=10)
		tenseStretch = node.addAttr(attrName="tenseStretchResistance", attrType="float",
		                            min=1.0, dv=100)
		# curve attributes
		baseSpans = node.addAttr(attrName="baseSpans", attrType="int", dv=5)
		degree = node.addAttr(attrName="degree", attrType="int", dv=2)
		node.con(baseSpans, self.rebuild + ".spans")
		node.con(degree, self.rebuild + ".degree")
		node.con(degree, self.hair.follicle + ".degree")

		# get activation value
		activePlug = self.computeActivation(userInput=active)

		# plug to show final activation for debugging
		crvTf = self.hair.outputLocalShape.transform
		activationDisplay = crvTf.addAttr(attrName="activation",
		                                  attrType="float")
		crvTf.con(activePlug, activationDisplay)

		# dynamic computation
		constant = ECA("addDoubleLinear", n="constant")
		constant.set("input1", 1)

		# stretch resistance
		stretchPlug = plug.blendFloatPlugs(
			plugList=[restStretch, tenseStretch],
			blender=activePlug,	name=self.name + "_stretchResist")
		node.con(stretchPlug, self.hair + ".stretchResistance")

		lengthPlug = plug.blendFloatPlugs(
			plugList=[constant + ".input1", length],
			blender=activePlug, name=self.name + "_targetLength" )
		node.con(lengthPlug, self.hair + ".restLengthScale")



		# constrain to curve
		pci = curve.curveRivet(self.ctrl.root, baseTf, uVal=0.5, )

		basePos = plug.vectorMatrixMultiply(
			vector=self.ctrl.first + ".translate",
		    matrix=self.ctrl.root + ".matrix",
			normalise=False)
		self.ctrlVector = plug.vecFromTo(pci + ".position",
		                                 basePos)

		# other hair attributes
		node.addAttr(attrName="pointLock", attrType="int", min=0, max=3, dv=0)
		node.con("pointLock", self.hair.follicle + ".pointLock")
		node.addAttr(attrName="bendResistance", attrType="float",
		             min=0, max=1, dv=0)
		node.con("bendResistance", self.hair + ".bendResistance")
		plugs = (#self.hair.follicle + ".pointLock",
		         self.hair + ".damp",
		         #self.hair + ".bendResistance",
		         self.hair + ".startCurveAttract",
		         # self.hair + ".attractionScale[0].attractionScale_FloatValue",
		         # self.hair + ".attractionScale[1].attractionScale_FloatValue",
		         )
		for i in plugs:
			attr.copyAttr(i, self.ctrl.first)
		self.ctrl.first.addAttr(attrName="startAttract", attrType="float",
		                        min=0, max=1.0, dv=1.0)
		self.ctrl.first.addAttr(attrName="endAttract", attrType="float",
		                        min=0, max=1.0, dv=1.0)
		self.ctrl.first.con("startAttract",
		        self.hair + ".attractionScale[0].attractionScale_FloatValue",)
		self.ctrl.first.con("endAttract",
		        self.hair + ".attractionScale[1].attractionScale_FloatValue", )



	def computeActivation(self, userInput=""):
		"""computes activation value for muscle, based on loads of stuff"""
		return userInput


	def setup(self):
		"""creates all internal systems for muscle"""

		# hair settings
		self.hair.follicle.set("startDirection", 1) # input curve
		self.hair.follicle.set("restPose", 3) # from curve
		self.hair.set("collisionFlag", 1) # vertex
		self.hair.set("selfCollisionFlag", 1) # vertex
		#self.hair.set("ignoreSolverGravity", 1)
		self.hair.set("ignoreSolverWind", 1)

		self.hair.outputLocalShape.transform.parentTo( self.setupGrp )

		# add curve rebuild
		rebuild = ECA("rebuildCurve", n=self.name+"_rebuild")


		pass


	def makeCurveSwollness(self, activationPlug):
		"""computes the clump width scale for curve p u m p
		bias - curve param at which thickness is greatest
		max - maximum thickness at full activation
		min - guess
		bulgeSpread - lateral shape of bulge along curve
		bulgeFactor - not used. how much second points inherit bulge.
			this is already enough control.
		"""
		bias = 0.5
		swellCurve = self.hair.outputLocalShape.shape.getShapeLayer()


	"""layers are dynamic collision -> naive bulge"""

	def makeJointHenchness(self, activationPlug):
		"""how much should joints scale during activation"""


	def makeJoints(self, res=None):
		"""create joints on muscle curve"""
		res = res or self.jointRes
		step = 1.0 / float(res - 1)
		joints = []
		for i in range(res):
			u = step * i
			joint = ECA("joint",
			            n=self.name + "_u{}_".format(u))
			# scale joint to be usable in scene
			scale = beauty.getUsableScale(self.hair.outputLocalShape,
			                              factor=0.1)
			joint.set("radius", scale)
			curve.curveRivet(joint, self.hair.outputLocalShape,
			                 u, upVectorSource=self.ctrlVector,
			                 tidyGrp=self.techGrp)
			joints.append(joint)
		return joints


	def makeDisplay(self):
		""" set colours, cv display etc """
		self.hair.outputLocalShape.setColour( self.muscleColour )
		self.hair.outputLocalShape.showCVs(1)
		for i in self.joints:
			i.setColour( self.muscleColour )


	@staticmethod
	def fromCurve(crv):
		"""regenerate a muscle object from a curve"""






"""
these muscles will communicate the drive and soul of the people we create - 
they need to be good.
activation value is determined by multiple factors:
	- derivative of change in muscle length
	- override user ripped-ness factor (please don't just ram it to 10)
	- maybe eventually distance between limb under dynamics and target,
		although that's taken care of mostly by derivative as well
	- sparse peak noise
	
activation drives a bulge vector (or optional blend to a tensed curve shape?)
ALTERNATIVELY, activation drives the goal length of the curve.

muscle expansion is then found through the change in length of the curve
we transfer this to joint scaling as approximation of volume preservation
this is also controlled by a ramp

bulge vector is also taken as upvector for muscle, with main vector
between start and end

joint resolution is how many joints to create
joint rivet kernel may be varied to account for twisty muscles like linguini

these barely need to be dynamic, just for the tension stuff, maybe collision
in hero scenes
investigate deltamushed poly ribbons instead
investigated lol, very not viable


	"""

class MuscleSheet(Muscle):
	"""??????
	definitely necessary
	polygon cloth version of muscle system
	"""