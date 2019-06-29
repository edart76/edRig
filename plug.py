"""operations working on plugs as live operation components"""

from maya import cmds
import maya.api.OpenMaya as om
from edRig import core, attr
from edRig.node import ECA, AbsoluteNode, PlugObject

def conOrSet(driver, driven):
	"""if EITHER is a static value, the opposite will be set as a plug"""
	args = (driver, driven)
	plugs = [core.isPlug(i) for i in args]
	if not any(plugs):
		raise RuntimeError("no plugs passed to conOrSet {}, {}".format(
			driver, driven))
	if all(plugs):
		attr.con(driver, driven)

	else:
		# lol
		val, plug = (args[i] if plugs[0] else args[not i] for i in plugs)
		attr.setAttr(plug, attrValue=val)

def vecFromTo(startPlug, endPlug):
	"""get vector between two plugs"""
	vec = ECA("plusMinusAverage", name="vecFrom_{}_{}".format(
		startPlug, endPlug))
	vec.set("operation", "subtract") #smart enum setting bois :D
	vec.con(endPlug, vec+".input3D[0]")
	vec.con(startPlug, vec+".input3D[1]")
	return vec+".output3D"


def plugCondition(val1, val2, operation="greaterThan"):
	"""compares conditions"""

def plugMin(*args):
	"""gets minimum of a set of plugs"""

def plugAdd(*args):
	"""adds set of plugs"""

def plugAverage(*args):
	"""gets average of plugs"""

def plugDistance(a, b=None):
	"""return euclidean distance between positions"""
	distance = ECA("distanceBetween")
	distance.conOrSet(a, distance+".point1")
	if b:
		distance.conOrSet(b, distance+".point2")
	return distance+".distance"


def reversePlug(plug):
	"""returns 1 - plug"""
	rev = ECA("reverse", n=plug+"_reverse")
	attr.con(plug, rev+".inputX")
	return rev+".outputX"

def periodicSignalFromPlug(plug, period=1.0, amplitude=1.0,
                           profile="linear"):
	"""creates a repeating 0-1 signal from float plug using
	animCurve node"""
	profiles = ("linear", "sine", "cosine", "tan")
	curve = ECA("animCurveUU")

