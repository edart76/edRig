""" base class, likely temporary to ease the pain
of trying to work with a solver system in tesserae

tesserae flow goes like this (for now):

nucleus -> DynamicOps, colliders
all colliders affect all elements, for now

eventually replace this with op sets, but those don't work yet

"""

from edRig import cmds, om, AbsoluteNode, ECA
from edRig.tesserae.ops import layer

from edRig import dynamics, muscle


class DynamicOp(layer.LayerOp):
	"""base for dynamics"""
	def __init__(self, *args, **kwargs):
		super(DynamicOp, self).__init__(*args, **kwargs)
		self.element = None

	def defineAttrs(self):
		self.addInput(name="nucleus", dataType="message",
		              desc="connect to common NucleusOp")
		self.addOutput(name="element", dataType="message",
		               desc="dynamic element - hair, cloth etc")

	def getNucleus(self):
		""" return the nucleus used for all
		connected dynamic ops """
		if not self.getInput("nucleus").connections:
			return None
		return self.getInput("nucleus").getConnectedAttrs[0].node.nucleus

	# oof

	def execute(self):
		self.nucleus = self.getNucleus()
		if not self.nucleus:
			raise RuntimeError("no nucleus connected to {}".format(self.opName))


class NucleusOp( DynamicOp ):
	""" creates a nucleus to feed further dynamics ops
	inherits for correctness' sake, overrides everything"""

	def __init__(self, *args, **kwargs):
		super(NucleusOp, self).__init__(*args, **kwargs)
		self.nucleus = None

	def defineAttrs(self):
		self.addOutput(name="nucleus", dataType="message",
		               desc="used to look up common nucleus node")

	def execute(self):
		self.nucleus = dynamics.Nucleus.create(
			name=self.opName + "_nucleus")
		self.getOutput("nucleus").plug = self.nucleus + ".message"
		self.remember(infoName="nucleus", infoType="attr",
		              nodes=[self.nucleus])

	def getNucleus(self):
		return self.nucleus


class ColliderOp( DynamicOp ):

	def defineAttrs(self):
		super(ColliderOp, self).defineSettings()
		self.addInput("collider2D", dataType="2D")

	def execute(self):
		super(ColliderOp, self).execute()
		self.collider = dynamics.NCollider.create(self.opName+"_collider")
		self.collider.connectInputShape(
			self.getInput("collider2D").plug )
		self.collider.connectToNucleus( self.nucleus )

		self.remember(infoName="colliderAttrs", infoType="attribute",
		              nodes=[self.collider])
		self.getInput("element").plug = self.collider + ".message"
		self.element = self.collider


class MuscleOp( DynamicOp ):

	def defineAttrs(self):
		super(MuscleOp, self).defineSettings()
		self.addInput("input1D", dataType="1D",
		              desc="curve with which to drive muscle")

	def execute(self):
		super(MuscleOp, self).execute()
		self.muscle = muscle.MuscleCurve.create(
			baseCrvPlug=self.getInput("input1D").plug,
			nucleus=self.nucleus,
			name=self.opName+"_muscle"
		)
		self.remember(infoName="hair", infoType="attr",
		              nodes=[self.muscle.hair])
		self.remember(infoName="ctrl", infoType="attr",
		              nodes=[self.muscle.ctrl.first])
		self.remember(infoName="ctrl", infoType="shape",
		              nodes=[self.muscle.ctrl.first])

		self.getInput("element").plug = self.muscle.hair + ".message"
		self.element = self.muscle.hair

class DynamicConstraintOp( DynamicOp ):
	""" constraining dynamic elements """

	def defineAttrs(self):
		array = self.addInput(name="elements", dataType="message",
		              hType="array", desc="elements to constrain")
		array.setChildKwargs(dataType="message", desc="constrained element")

	def onSync(self):
		array = self.getInput("elements")
		n = len(array.getConnectedAttrs)
		specList = [ {"name" : "element{}".format(i)} for i in range(n+1)]
		array.matchArrayToSpec( spec=specList )

	def execute(self):
		nConnected = len(self.getInput("elements").getConnectedAttrs)
		if not nConnected:
			raise RuntimeError("no elements given to connect")

