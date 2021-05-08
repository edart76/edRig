"""tests for AbsoluteNode
sick of it breaking"""

from edRig import AbsoluteNode, ECA
from edRig.lib.python import StringLike
from edRig.test import test

from maya import cmds

@test
def testStringLike():
	""" tests the core of all enhanced string stuff """

	base = "base"
	baseLike = StringLike( base=base)
	print(baseLike)

	print(( "isinstance baseLike string : {}".format(isinstance(baseLike, str))))
	#assert isinstance("test", str)
	#assert  isinstance(baseLike, str)

	"""------- NOTA BENE --------"""
	print(baseLike + base) # THIS WORKS - calls __add__ of stringLike
	print(base + baseLike) # THIS DOES NOT - calls __add__ of STRING
	""" how do we do this """


@test
def testAbsoluteNode():
	"""tests the live refresh capability"""
	parent = ECA("joint", n="parent")
	print("parent is {}".format(parent))

	child = ECA("joint", n="child")
	print("child is {}".format(child))

	print(( cmds.ls( "child")))

	child.parentTo(parent)

	print("test" + child)

	print("parent is " + parent + ", child is " + child)
	print("format parent is {}, child is {}".format(parent, child))


