from edRig import AbsoluteNode, ECA, curve, beauty, attr
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

		return muscle

	def setup(self):
		"""creates all internal systems for muscle"""
		baseRebuild = ECA("rebuildCurve")
		baseShapePlug = attr.getImmediatePast(
			self.hair.inputShapePlug, wantPlug=True	)[0]
		baseRebuild.con(baseShapePlug, "inputCurve" )
		baseRebuild.set("degree", 1) # linear
		baseRebuild.con("outputCurve", self.hair.inputShapePlug)

		ctrl = AbsoluteNode( self.hair.outputLocalShape.transform )
		spanPlug = ctrl.addAttr(attrName="baseSpans", attrType="int", dv=4)
		ctrl.con(spanPlug, baseRebuild + ".spans")



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