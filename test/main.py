from edRig.test import *
from edRig.test.node import testAbsoluteNode
from edRig.test.tesserae import testTesserae
from edRig.test import tool


def testAll():
	print "testFuncs are {}".format(testFuncs)
	return [i() for i in testFuncs]

def testSpecific():
	""" test specific user-defined function """
	#testTesserae()
	reload(tool)
	tool.testPulley()



