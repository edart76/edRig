from edRig.tests import *
from edRig.tests.node import testAbsoluteNode

def testAll():
	print "testFuncs are {}".format(testFuncs)
	return [i() for i in testFuncs]