# literacy is important
import io
import maya.cmds as cmds
import ast
import edRig.core as core
from edRig import pipeline
from edRig.structures import SafeDict
import json
import copy
import inspect
import pprint

import os

dataFolder = "F:/all projects desktop/common/edCode/edRig/data/"
tempPath = dataFolder + "tempData"

def checkJsonSuffix(path):
	if ".json" in path:
		path = path.split(".json")[0]
	return path + ".json"

# control versioning with a separate system
def ioinfo(name="", mode="in", info=None, path=tempPath):
	# read and write generic info to and from maya
	# name is key in file dictionary
	goss = {}
	path = checkJsonSuffix(path)

	if mode == "in":
		print ""
		with open("{}".format(path)) as file:
			#goss = json.load(file)
			#goss = json.loads(eval(file.read()))
			goss = file.read()
			pass
		print "goss is type {}".format(type(goss))
		if isinstance(goss, dict):
			print "goss is dict"
			return goss

		try:
			goss = ast.literal_eval(str(goss))
			print "goss is type {}".format(type(goss))

			# while isinstance(goss, str):
			# 	goss = eval(goss)
			print "new goss is type {}".format(type(goss))
		except Exception as e:
			print "ERROR in attrio reading from file {}".format(path)
			print "error is {}".format(str(e))
		#print "goss is {}".format(goss)
		return goss

	elif mode == "out":

		file = io.open(path, "w+b")
		#file.write(pprint.pformat(json.dumps(info, indent=3), indent=3))
		file.write(pprint.pformat(info, indent=3))
		#file.write(json.dump(pprint.pformat(info, indent=3)))
		#file.write(pprint.pformat(str(info), indent=1))
		file.close()

	else:
		raise RuntimeError("no valid mode ('in' or 'out') to ioinfo")



def ioinfo2(name="", mode="in", info=None, path=tempPath):
	# using more advanced fullSerialise and fullRestore

	if mode == "in":
		goss = ioinfo(mode="in", path=path)
		return fullRestore(goss)

	elif mode == "out":
		serialised = fullSerialise(info)
		ioinfo(mode="out", info=serialised, path=path)


def totalio(node, mode, infoName="", path=tempPath, apply=False, parent=""):
	# the power to exist outside of maya
	# to be abstracted to information, and then to be reborn
	if not infoName:
		name = node
		# bad idea

	# DO NOT store information under a key of the node's maya string
	# infoName is reliable key name

	nodeInfo = {}
	if mode == "out":
		# first load the file to avoid overriding stuff
		nodeInfo["name"] = node
		nodeInfo["type"] = cmds.nodeType(node)
		getNodeAttrsAsDict(node, nodeInfo)
		nodeInfo["createdBy"] = "totalio"
		ioinfo(infoName, "out", info=nodeInfo, path=path)
		# this will set the value of top-level key "infoName" to nodeInfo dict

	elif mode == "in":
		nodeInfo = ioinfo(infoName, "in", path=path, info=nodeInfo)
		# this will set the value of top-level key "infoName" to nodeInfo
		name = nodeInfo["name"]
		if nodeInfo["createdBy"] != "totalio":
			print "totalio used on {}, a non-totalio image, proceed at own risk".format(
				node)
		if apply:
			if not cmds.objExists(node):
				cmds.createNode(nodeInfo["type"], n=nodeInfo["name"])
			setNodeAttrsFromDict(node, nodeInfo)

	return nodeInfo

	# add better grouping of dictionaries within single files, per operation

	# add support if info is not found or doesn't exist,
	# add support for creating attributes if they do not exist by default
	# do total getattr to construct dictionary of addattr arguments


def getNodeAttrsAsDict(node, nodeInfo=None, **kwargs):
	# add in support to only get useful stuff
	# no one wants to know if your node is historically interesting
	for attr in cmds.listAttr(node):
		nodeInfo["attrs"][attr] = cmds.getAttr(node + "." + attr)
	return nodeInfo


def setNodeAttrsFromDict(node, nodeInfo):
	# do we want name, or automatic creation?
	for attr in nodeInfo["attrs"]:
		cmds.setAttr(node + "." + attr, nodeInfo["attrs"][attr])
	return node


def getData(infoName, path=tempPath):
	# look for a key in the datafile and return its value, else return False
	print "GET DATA PATH IS {}".format(path)
	goss = ioinfo(mode="in", path=path)

	print "GET DATA GOSS IS {}".format(goss)
	if not goss:
		print "GET DATA GOT NO DATA"
		raise RuntimeError
		#return None
	# returns the whole dict
	elif infoName in goss.keys():
		print "GET DATA GOT GOSS {}".format(goss[infoName])
		return goss[infoName]
	else:
		return None


def updateData(infoName, data, path=tempPath):
	# open the datafile and update it
	goss = ioinfo(mode="in", path=path)
	if infoName not in goss.keys():
		goss[infoName] = {}
	goss[infoName].update(data)
	ioinfo(mode="out", path=path, info=goss)
	# welcome to hell


def renameFile(old="", new=""):
	"""expects entire paths"""
	return pipeline.renameFile(old, new, suffix="json")

def deleteFile(path):
	path = checkJsonSuffix(path)
	print ""
	print "#### D E L E T I N G ####"
	print "target is {}".format(path)
	os.remove(path)
	print ""


def makeBlankFile(path=tempPath):
	# just to set things up
	randomFact = "crocodiles have two aortas"
	blankDict = {"did you know ": randomFact}

	ioinfo(path=path, mode="out", info=blankDict)


def checkFileExists(filePath):
	print "testPath is {}".format(filePath)
	if os.path.exists(filePath + ".json"):
		return True
	else:
		return False
