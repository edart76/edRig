from edRig.tests import *
from edRig.tests.node import testAbsoluteNode
from edRig.tests.tesserae import testTesserae
from edRig.tests import tool


def testAll():
	print "testFuncs are {}".format(testFuncs)
	return [i() for i in testFuncs]

def testSpecific():
	""" test specific user-defined function """
	#testTesserae()
	reload(tool)
	tool.testPulley()



