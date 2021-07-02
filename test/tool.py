""" tests for the various tools and autorigs """

import random

from edRig.test import test
from edRig import cmds, om, EdNode, ECA

from edRig.tool import pulley
import importlib
importlib.reload(pulley)

@test
def testPulley(nWheels=4, randRange=10.0, flat=True):
	""" scatter random wheels of random radius and connect them """
	system = pulley.PulleySystem("testSystem")
	for i in range(nWheels):
		wheel = system.addWheel(name="test{}wheel".format(i))
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
		point.set("radius", 1 + random.random())
		#point.set("flip", 1)
	system.link()
	cmds.setAttr("test1wheelpointInput.radius", 3.0)
	#cmds.setAttr("test0wheelpointInput.radius", 0.0001)



