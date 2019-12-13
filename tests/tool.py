""" tests for the various tools and autorigs """

import random

from edRig.tests import test
from edRig import cmds, om, AbsoluteNode, ECA

from edRig.tools import pulley

@test
def testPulley(nWheels=10, randRange=10.0, flat=True):
	""" scatter random wheels of random radius and connect them """

	for i in range(nWheels):
		point = ECA("locator", n="base{}Point".format(i))
		axes = "XY" if flat else "XYZ"
		for a in axes:
			point.set("translate" + a, random.random() * randRange )

		# create wheel setup ---
		wheel = pulley.Wheel()



