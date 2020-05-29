from edRig.tests import *
from edRig.tests.node import testAbsoluteNode
from edRig.tests.tesserae import testTesserae

def testAll():
	print "testFuncs are {}".format(testFuncs)
	return [i() for i in testFuncs]

def testSpecific():
	""" test specific user-defined function """
	testTesserae()


