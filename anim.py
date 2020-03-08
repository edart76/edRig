""" functions for working with animation keys, saving out anim etc """
from edRig import cmds, om, AbsoluteNode, ECA
from edRig import attr, plug


def keyPlug(keyPlug=None, time=1, value=0.0):
	""" basic way to insert key - no regard for tangents """
	node = keyPlug.split(".")[0]
	at = ".".join(keyPlug.split(".")[1:])
	# will need checking for float vs time based curves
	cmds.setKeyframe(node, attribute=at, time=time, float=time, value=value)


class AnimCurve(AbsoluteNode):
	""" base class for wrapping anim curves """

	def __init__(self, node=""):
		super(AnimCurve, self).__init__(node=node)
		pass

	def setMObject(self, obj):
		""" create MFnAnimCurve for this node """
		super(AnimCurve, self).setMObject(obj)
		self.MFnAnim = om.MFnAnimCurve(obj)