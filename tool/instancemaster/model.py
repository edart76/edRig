# central data model for managing instances
from maya import cmds
import maya.api.OpenMaya as om
from edRig import attr, transform
from edRig.core import invokeNode
from edRig.node import AbsoluteNode, ECA
from PySide2 import QtCore
from edRig.layers.setups import InvokedNode

from edRig.tesserae.abstractgraph import AbstractGraph, AbstractGraphExecutionManager
from edRig.tesserae.abstractnode import AbstractNode, AbstractAttr
from edRig.tesserae.abstractedge import AbstractEdge
"""no way can i actually do this
graph does not execute
or does it lol

fuck it yes i will build a node graph out of model instances
"""



"""
SO
to start, imagine random group in scene, with transforms, pivot, everything
A_grp
--B_grp
----B_geo
--A_geo

you like this group and want to make it an instance master
you right click, choose ("make selected master")
 -- one window appears: "name new master"
 ---- offset hierarchy is created around A_grp, has ONLY ITS OWN transforms zeroed
 back to (hopefully) neutral
 ------- instance is created, parented under new globalOffset_grp, globalOffset is
 reset to the transforms held by original A_grp
 

offset hierarchy is this:
globalOffset_grp # EVERYTHING BELOW IS AN INSTANCE
--commonOffset_grp
----A_grp
------etc


masters can never include other masters
instances can never directly be masters
in constructing a complex object, a new master will be created for every stage of its
combination
"""

class InstanceGraph(AbstractGraph):
	"""i run this place
	this is only to store and track the instance structure in scene"""

	def __init__(self, name="InstanceGraph"):
		super(InstanceGraph, self).__init__(name=name)
		pass # whatever

	def initGraph(self):
		"""do nothing for now"""
		pass

	def serialise(self):
		"""create a node in the scene to hold the string info"""

	@staticmethod
	def fromDict(regen):
		"""read back string info from scene"""

class MasterNode(AbstractNode):
	"""tracks its own name, and its relationship in hierarchy,
	and all instances that DIRECTLY depend on it
	that's it"""
	
	def __init__(self, graph, name=None, rootTf=None):
		"""pass root (individual offset group) above component you want to instance"""
		super(MasterNode, self).__init__(graph, name)
		self.rootTf = rootTf

		self.addInput("reliesUpon")
		self.addOutput("supports")

	def getInstances(self):
		"""crawl string connections FROM rootTf TO instance rootTfs"""
		future = attr.getImmediateFuture(self.rootTf+".instances") # returns node, plug
		return [ i[0] for i in future]

	def addInstance(self, instanceName):
		"""create new instance from rootTf, add an attribute to it, make string connection"""
		newTf = cmds.duplicate(self.rootTf, n=instanceName, instanceLeaf=True)
		attr.makeStringConnection(self.rootTf, newTf,
		                          startName="instances", endName="master")
		return newTf


	def initSettings(self):
		pass
	def makeReal(self, realInstance):
		pass


class SceneInstanceModel(object):
	"""tracks supported instances in the maya scene"""
	def __init__(self, parent=None, ui=None):
		# super(SceneInstanceModel, self).__init__(parent)
		self.masters = self.listAllMasters()
		self.updateMasterList()
		self.ui = ui
		#self.children = {}
		#self.masterGrp = InvokedNode("InstanceMaster_masters")
		#self.catalogue = {} # Abs(network node) : IM object

		self.wireSignals()

	def wireSignals(self):
		self.ui.onNewMaster.connect(self.makeSelectedNewMaster)

	# def objectFromNetwork(self, network):
	# 	return self.catalogue[network]

	def updateMasterList(self):
		self.masters = self.listAllMasters()

	def makeSelectedNewMaster(self, target=None):
		if not target:
			target = cmds.ls(sl=True)
			if not target:
				print "nothing selected, no new master to create"
				return
			target = target[0]
		masterName = raw_input("Name new instance master")
		if not masterName or not self.checkMasterNameValid(masterName):
			print "no valid name input, terminating"
			return
		print "making master from {}".format(target)

		# # first make IM object and offsets
		# master = MasterItem(target, self, masterName)



		# copy = cmds.instance(target, n=target+"_instance")
		# # zero transforms of master, parent to masterGrp and hide it
		# cmds.parent(target, self.masterGrp)
		# cmds.makeIdentity(target, t=True, r=True, s=True)
		# cmds.setAttr(target+".visibility", 0)

		# add offset hierarchy
		pos = cmds.xform(target, q=True, ws=True, t=True)
		masterOffset = self.addOffsetGrp(target, name=masterName+"_master")
		# if zeroing becomes an issue, xform back to pos

		attr.addTag(masterOffset, tagName="InstanceMaster", tagContent=masterName)
		newName = masterName+"_instance"
		copyOffset = self.makeTagInstance(masterOffset, newName)
		cmds.xform(masterOffset, ws=True, t=(0, 0, 0), a=True)
		cmds.setAttr(masterOffset+".visibility", 0)

		# add offset group to master, then instance offset group itself

	def addOffsetGrp(self, dag, name=None, freeze=True):
		"""creates a new node, match target, insert in hierarchy"""
		newname = name or dag+"_offset"
		offset = ECA("transform", name=newname)
		transform.matchXforms(offset, dag)
		parent = cmds.listRelatives(dag, parent=True)
		if parent: # could be in world
			cmds.parent(offset, parent[0])
		cmds.makeIdentity(offset, apply=True)
		cmds.parent(dag, offset)
		return offset

	def makeTagInstance(self, master, instanceName=None):
		"""creates instances and tags them"""
		name = instanceName or master+"_instance"
		copy = cmds.instance(master, n=name)[0]
		plug = attr.addTag(copy, "InstanceMaster")

		# master already has instanceMaster attribute
		cmds.connectAttr(master+".InstanceMaster", plug)
		return copy

	def checkMasterNameValid(self, name):
		"""checks master name is maya-friendly and not a duplicate"""
		if name in self.listAllMasters().keys():
			return False
		return True



	def refreshInstanceFromMaster(self, instance, master):
		"""repopulates an instance with its master copy
		relies on the master already being refreshed if it contains
		instances - this must be run from hierarchy leaves upwards"""
		instParent = cmds.listRelatives(instance)

	def getRefreshOrder(self, refreshList=None):
		"""consider simple diamond-ish pattern
				   / - masterB
		masterA -<              \
				   \ ----------- masterC

		we need only check if nodes have been refreshed at all -
		at outset mark all as dirty

		refresh masterA -> look for all nodes it contains
							-> if not dirty, refresh those

		sorted
		"""






	@staticmethod
	def tagAsMaster(tagNode, masterName="newMaster"):
		attr.addTag(tagNode, tagName="IM_master", tagContent=masterName)

	@staticmethod
	def tagAsChildInstance(tagNode, masterName="newMaster"):
		attr.addTag(tagNode, tagName="IM_child", tagContent=masterName)

	@staticmethod
	def addOffsetHierarchy(target):
		# pre, post-instance?
		parent = cmds.listRelatives(target, p=True)
		offsetGrp = ECA("transform", name=target+"_offsetA")
		transform.matchXforms(offsetGrp, target, pos=True, rot=True)
		cmds.parent()
		pass



	@staticmethod
	def listAllMasters():
		found = {}
		masters = attr.listTaggedNodes(searchTag="IM_master", searchType="transform")
		for i in masters:
			name = attr.getTag(i, tagName="IM_master")
			found[name] = i
		return found

	@property
	def masterGrp(self):
		return invokeNode(name="InstanceMaster_masters", type="transform")






