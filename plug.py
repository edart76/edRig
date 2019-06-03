"""operations working on plugs as live operation components"""

from maya import cmds
from edRig import core, attr

def conOrSet(targetPlug, driver):
	"""targetPlug will be the recipient of the operation
	driver will drive it, by connection if plug or setAttr if not"""
	if core.isPlug(driver):
		attr.con(driver, targetPlug)
	else:
		attr.setAttr(targetPlug, driver)

def plugCondition(val1, val2, operation="greaterThan"):
	"""compares conditions"""