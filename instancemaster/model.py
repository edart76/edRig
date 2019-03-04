# central data model for managing instances
from maya import cmds
import maya.api.OpenMaya as om
from edRig import attr, transform
from edRig.core import AbsoluteNode, ECA
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

class InstanceMasterObject(object):
	"""defines access for global and instance offsets"""

	def __init__(self, target, model):
		"""associates object with target maya dag node"""
		self.name = "new_IMobject"
		self.model = model
		self.realNode = AbsoluteNode(target)
		self.realParent = cmds.listRelatives(target, parent=True)
		self.globalOffset = None
		self.instanceOffset = None
		self.isMaster = False
		self.isInstance = False # both CANNOT be true

		# network nodes used to show relationship in graph and regenerate
		self.network = ECA("network", self.name+"_network")
		self.makeNetwork()

	def makeOffsets(self):
		"""creates new groups above target, with global offset matched to target"""
		self.globalOffset = ECA("transform", self.name+"globalOffset")
		self.instanceOffset = ECA("transform", self.name + "instanceOffset")
		cmds.parent(self.instanceOffset, self.globalOffset)
		transform.matchXforms(source=self.realNode, target=self.globalOffset)

		# maybe move these - insert groups
		if self.realParent:
			cmds.parent(self.globalOffset, self.realParent)
		cmds.parent(self.realNode, self.instanceOffset)

		cmds.connectAttr(self.globalOffset+".message", self.network+".globalOffset")

	def makeNetwork(self):
		attr.addTag(self.network, "InstanceMasterObject")
		attr.addAttr(self.network, attrName="globalOffset", attrType="string")



class MasterItem(InstanceMasterObject):
	"""object for static master instances"""
	def __init__(self, target, model):
		super(MasterItem, self).__init__(target, model)
		self.isMaster = True
		# self.children = [] # lists only instances of this specific master

	def makeMaster(self, name):
		"""called after operation has been verified"""
		dummyMarker = ECA("transform", "newMaster_"+name+"_dummy")
		transform.matchXforms(source=self.globalOffset, target=dummyMarker)
		newInstance = self.makeInstance(name=self.name+"_newInstance")

	@property
	def children(self):
		networks = attr.getImmediateFuture(self.network+".children")
		networks = [i[0] for i in networks] # get nodes from tuples
		return [self.model.objectFromNetwork(i) for i in networks]


	def makeNetwork(self):
		super(MasterItem, self).makeNetwork()
		attr.addAttr(self.network, attrType="string", attrName="children")

	def makeInstance(self, name="newInstance"):
		"""splits off a new instance of this master"""
		newGlobal = None






class InstanceItem(InstanceMasterObject):
	"""wrapper for traversing instance tree"""
	def __init__(self, target, parent):
		super(InstanceItem, self).__init__(target)
		self.parent = parent


class SceneInstanceModel(object):
	"""tracks supported instances in the maya scene"""
	def __init__(self, parent=None, ui=None):
		# super(SceneInstanceModel, self).__init__(parent)
		self.masters = self.listAllMasters()
		self.instances = self.listAllChildren()
		self.updateMasterList()
		self.ui = ui
		#self.children = {}
		self.masterGrp = InvokedNode("InstanceMaster_masters")
		self.catalogue = {} # Abs(network node) : IM object
		pass

	def objectFromNetwork(self, network):
		return self.catalogue[network]

	def updateMasterList(self):
		self.masters = self.listAllMasters()

	def makeNewMaster(self, target):
		masterName = raw_input("Name new instance master")
		if not masterName or not self.checkMasterNameValid(masterName):
			print "no valid name input, terminating"
			return

		# first make IM object and offsets


		# copy = cmds.instance(target, n=target+"_instance")
		# # zero transforms of master, parent to masterGrp and hide it
		# cmds.parent(target, self.masterGrp)
		# cmds.makeIdentity(target, t=True, r=True, s=True)
		# cmds.setAttr(target+".visibility", 0)
		#
		# # add offset hierarchy
		# self.addOffsetHierarchy()

	def checkMasterNameValid(self, name):
		"""checks master name is maya-friendly and not a duplicate"""
		#if name in



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

	def listAllChildren(self):
		"""returns dict of masterName:[instanceItems]"""

	@staticmethod
	def listAllMasters():
		found = {}
		masters = attr.listTaggedNodes(searchTag="IM_master", searchType="transform")
		for i in masters:
			name = attr.getTag(i, tagName="IM_master")
			found[name] = i
		return found






