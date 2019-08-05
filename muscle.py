from edRig import AbsoluteNode, ECA
from edRig.dynamics import Nucleus, NHair, makeCurveDynamic

class MuscleCurve(object):
	"""dynamic curve making relative motions according to changes in length
	includes a bulge vector and ramp"""

	def __init__(self, inputPlug, refPlug):
		pass

	@staticmethod
	def create(baseCrv, nucleus=None,
	           timeInput="time1.outTime",
	           name="testMuscle"
	           ):
		hair = makeCurveDynamic(baseCrv, live=True, timeInput=timeInput,
		                 nucleus=nucleus, name=name)
		return hair


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

curve resolution is number of curve CVs
joint resolution is how many joints to create
joint rivet kernel may be varied to account for twisty muscles like linguini

these barely need to be dynamic, just for the tension stuff, maybe collision
in hero scenes
investigate deltamushed poly ribbons instead


	"""

class MuscleSheet(object):
	"""??????
	probably not necessary"""