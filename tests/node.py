"""tests for AbsoluteNode
sick of it breaking"""

from edRig import AbsoluteNode, ECA

def testAbsoluteNode():
	"""tests the live refresh capability"""
	parent = ECA("joint", n="parent")
	print "parent is {}".format(parent)

	child = ECA("joint", n="child")
	print "child is {}".format(child)

	child.parentTo(parent)

	print "parent is " + parent + ", child is " + child

