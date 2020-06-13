""" tests for the various tools and autorigs """

import random

from edRig.tests import test
from edRig import cmds, om, AbsoluteNode, ECA

from edRig.tools import pulley
reload(pulley)

@test
def testPulley(nWheels=4, randRange=10.0, flat=True):
	""" scatter random wheels of random radius and connect them """
	system = pulley.PulleySystem("testSystem")
	for i in range(nWheels):
		system.addWheel(name="test{}wheel".format(i))
	system.build()

	positions = [(3, 0, 0),
	             (0, 3, 0),
	             (3, 6, 0),
	             (6, 3, 0)]
	for i in range(nWheels):
		#point = ECA("locator", n="base{}Point".format(i))
		wheel = system.wheels[i]
		point = wheel.pin
		axes = "XY" if flat else "XYZ"
		# for a in axes:
		# 	point.set("translate" + a, random.random() * randRange )
		point.set("translate", positions[i])
	system.link()




