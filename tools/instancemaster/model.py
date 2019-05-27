# central data model for managing instances
from maya import cmds
import maya.api.OpenMaya as om
from edRig import attr, transform
from edRig.core import invokeNode
from edRig.node import AbsoluteNode, ECA
from PySide2 import QtCore
from edRig.layers.setups import InvokedNode

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
#
# class InstanceMasterObject(object):
# 	"""defines access for global and instance offsets"""
#
# 	def __init__(self, target, model, name=None, setup=True):
# 		"""associates object with target maya dag node"""
# 		self.name = name or "new_IMobject"
# 		self.model = model
# 		self.realNode = AbsoluteNode(target)
#
# 		self.realParent = cmds.listRelatives(target, parent=True)
# 		self.globalOffset = None
# 		self.instanceOffset = None
# 		self.isMaster = False
# 		self.isInstance = False # both CANNOT be true
# 		self.network = None
#
# 		if setup:
# 			self.setup()
# 		else:
# 			self.regenerate()
#
# 	def setup(self):
# 		"""run on creation of instance, not regeneration"""
# 		attr.addTag(self.realNode, "InstanceMasterObject")
# 		# network nodes used to show relationship in graph and regenerate
# 		self.network = ECA("network", self.name+"_network")
# 		self.makeNetwork()
#
# 	def regenerate(self):
# 		test = attr.getImmediateNeighbours(self.realNode+".InstanceMasterObject_tag")
# 		self.network = [i for i in test if "network" in i][0]
#
# 	def makeOffsets(self):
# 		"""creates new groups above target, with global offset matched to target"""
# 		self.globalOffset = ECA("transform", self.name+"globalOffset")
# 		self.instanceOffset = ECA("transform", self.name + "instanceOffset")
# 		cmds.parent(self.instanceOffset, self.globalOffset)
# 		transform.matchXforms(source=self.realNode, target=self.globalOffset)
#
# 		# maybe move these - insert groups
# 		if self.realParent:
# 			cmds.parent(self.globalOffset, self.realParent)
# 		cmds.parent(self.realNode, self.instanceOffset)
#
# 		cmds.connectAttr(self.globalOffset+".message", self.network+".globalOffset")
#
# 	def makeNetwork(self):
# 		attr.addTag(self.network, "InstanceMasterObject")
# 		attr.addAttr(self.network, attrName="globalOffset", attrType="string")
# 		attr.addAttr(self.network, attrName="instanceNode", attrType="string")
#
# 		cmds.connectAttr(self.realNode+".InstanceMasterObject_tag",
# 		                 self.network+".instanceNode")
#
#
#
# class MasterItem(InstanceMasterObject):
# 	"""object for static master instances"""
# 	def __init__(self, target, model, name=None):
# 		super(MasterItem, self).__init__(target, model, name)
# 		self.isMaster = True
# 		#attr.addTag(self.realNode, "IM_master")
# 		SceneInstanceModel.tagAsMaster(self.realNode, self.name)
# 		# self.children = [] # lists only instances of this specific master
#
# 	def makeInstance(self, name):
# 		"""called after operation has been verified"""
# 		dummyMarker = ECA("transform", "newMaster_"+name+"_dummy")
# 		transform.matchXforms(source=self.globalOffset, target=dummyMarker)
# 		newInstance = self.makeInstance(name=self.name+"_newInstance")
#
# 	@property
# 	def children(self):
# 		networks = attr.getImmediateFuture(self.network+".children")
# 		networks = [i[0] for i in networks] # get nodes from tuples
# 		return [self.model.objectFromNetwork(i) for i in networks]
#
#
# 	def makeNetwork(self):
# 		super(MasterItem, self).makeNetwork()
# 		attr.addAttr(self.network, attrType="string", attrName="children")
#
# 	def makeInstance(self, name="newInstance"):
# 		"""splits off a new instance of this master"""
# 		newGlobal = cmds.instance(self.realNode, name=name)
#
#
#
#
#
#
#
# class InstanceItem(InstanceMasterObject):
# 	"""wrapper for traversing instance tree"""
# 	def __init__(self, target, parent):
# 		super(InstanceItem, self).__init__(target)
# 		self.parent = parent
#
# 	def makeNetwork(self):
# 		"""uses master's network"""
# 		pass
#

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
		"""repopulates an instance with its master copy"""
		instParent = cmds.listRelatives(instance)


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






