from edRig import AbsoluteNode, ECA, curve, beauty, attr, \
	control, plug, transform
from edRig.dynamics import Nucleus, NHair, makeCurveDynamic


class MuscleCurve(object):
	"""dynamic curve making relative motions according to changes in length
	includes a bulge vector and ramp"""

	# solvers to transfer muscle deformation to mesh
	transferSolvers = ("joints", "wire")
	upSolvers = ("target", "surfaceNormal")

	def __init__(self, hair, name="newMuscle",
	             collisionRigid=None,
	             jointRes=5):
		"""initialise with base hair system governing muscle behaviour"""
		self.hair = hair
		self.jointRes = jointRes
		self.name = name
		self.collider = collisionRigid
		pass

	@staticmethod
	def create(baseCrv, nucleus=None,
	           jointRes=5,
	           upSolver=None,
	           timeInput="time1.outTime",
	           name="testMuscle",
	           ):
		hair = makeCurveDynamic(baseCrv, live=True, timeInput=timeInput,
		                 nucleus=nucleus, name=name)
		muscle = MuscleCurve(hair, jointRes=jointRes,
		                     name=name)
		muscle.setup()
		muscle.makeJoints()
		muscle.makeControl()

		return muscle

	def makeControl(self):
		"""create control attributes"""
		self.ctrl = control.TileControl(name=self.name,
		                                colour=(56, 120, 256) )
		node = AbsoluteNode(self.ctrl.first)

		# set up muscle attributes
		# activation
		active = node.addAttr(attrName="activation", attrType="float", min=0, max=1, dv=0)
		length = node.addAttr(attrName="tensedLength", attrType="float", min=0, dv=1)
		restStretch = node.addAttr(attrName="restStretchResistance", attrType="float",
		                            min=1.0, dv=10)
		tenseStretch = node.addAttr(attrName="tenseStretchResistance", attrType="float",
		                            min=1.0, dv=100)
		# curve attributes
		baseSpans = node.addAttr(attrName="baseSpans", attrType="int", dv=5)

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
			blender=activePlug,
			name=self.name + "_stretchResist")
		node.con(stretchPlug, self.hair + ".stretchResistance")

		lengthPlug = plug.blendFloatPlugs(
			plugList=[constant + ".input1", length],
			blender=activePlug, name=self.name + "_targetLength" )
		node.con(lengthPlug, self.hair + ".restLengthScale")

		# connect basic curve stuff
		node.con(baseSpans, self.baseRebuild + ".spans")

	def computeActivation(self, userInput=""):
		"""computes activation value for muscle, based on loads of stuff"""
		return userInput


	def setup(self):
		"""creates all internal systems for muscle"""
		baseRebuild = ECA("rebuildCurve")
		baseShapePlug = attr.getImmediatePast(
			self.hair.inputShapePlug, wantPlug=True	)[0]
		baseRebuild.con(baseShapePlug, "inputCurve" )
		baseRebuild.set("degree", 1) # linear
		baseRebuild.con("outputCurve", self.hair.inputShapePlug)
		self.baseRebuild = baseRebuild

	def makeCurveSwollness(self, activationPlug):
		"""computes the clump width scale for curve p u m p
		bias - param at which thickness is greatest
		max - maximum thickness at full activation
		min - guess
		bulgeSpread - lateral shape of bulge along curve
		bulgeFactor - not used. how much second points inherit bulge.
			this is already enough control.
		"""
		bias = 0.5


	"""layers are dynamic collision -> naive bulge"""


	def makeJoints(self, res=None):
		"""create joints on muscle curve"""
		res = res or self.jointRes
		step = 1.0 / float(res - 1)
		for i in range(res):
			u = step * i
			joint = ECA("joint",
			            n=self.name + "_u{}_".format(u))
			# scale joint to be usable in scene
			scale = beauty.getUsableScale(self.hair.outputLocalShape,
			                              factor=0.1)
			joint.set("radius", scale)
			curve.curveRivet(joint, self.hair.outputLocalShape,
			                 u, )

	@staticmethod
	def fromCurve(crv):
		"""regenerate a muscle object from a curve"""






"""
these muscles will communicate the drive and soul of the people we create
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
investigated lol, not viable


	"""

class MuscleSheet(object):
	"""??????
	probably not necessary"""