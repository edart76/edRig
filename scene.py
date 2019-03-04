# operations for listing, grouping, adding to sets etc
from maya import cmds
#import maya.api.OpenMaya as om

def listTopNodes():
	return set(cmds.ls("|*", recursive=True))