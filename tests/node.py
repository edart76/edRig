"""tests for AbsoluteNode
sick of it breaking"""

from edRig import AbsoluteNode, ECA
from edRig.tests import test

@test
def testAbsoluteNode():
	"""tests the live refresh capability"""
	parent = ECA("joint", n="parent")
	print "parent is {}".format(parent)

	child = ECA("joint", n="child")
	print "child is {}".format(child)

	child.parentTo(parent)

	print "parent is " + parent + ", child is " + child
	print "format parent is {}, child is {}".format(parent, child)


