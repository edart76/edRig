"""AbsoluteNode and object-style nod wrappers"""
from maya import cmds
import maya.api.OpenMaya as om

from edRig.core import MObjectFrom, shapeFrom, tfFrom, stringFromMObject, ECN
from edRig import attr

def invokeNode(name="", type="", parent="", func=None):
	# print "core invokeNode looking for {}".format(name)
	if cmds.objExists(name):
		#print "found {}".format(name)
		return AbsoluteNode(name)
	if not func:
		func = ECA
	node = func(type, name=name)
	if parent and cmds.objExists(parent):
		#print "parenting invoked"
		cmds.parent(node, parent)
	return node


class AbsoluteNode(str):
	# DON'T LOSE YOUR WAAAAY

	allInfo = {
		"mesh" : {
			"inShape" : "inMesh",
			"outLocal" : "outMesh",
			"outWorld" : "worldMesh[0]"
		},
		"transform" : {
			"outLocal" : "matrix",
			"outWorld" : "worldMatrix[0]"
		}
	}

	def __new__(cls, node):
		# this is the stripped down fast version of pymel
		# print "type node is {}".format(type(node))
		# print "node is {}".format(node)
		if isinstance(node, AbsoluteNode):
			return node
		elif isinstance(node, list):
			print "node is list"
			return AbsoluteNode(node[0])
		elif isinstance(node, om.MObject):
			return AbsoluteNode.fromMObject(node)
		elif isinstance(node, unicode):
			return AbsoluteNode(str(node))
		absolute = str.__new__(cls, node)
		absolute.node = node
		if not cmds.objExists(node):
			print "{} DOES NOT EXIST - YER OFF THE MAP".format(node)
			absolute.refreshPath = absolute.returnBasicNode
			return absolute
		obj = MObjectFrom(node)
		absolute.setMObject(obj)

		# set custom nodeinfo
		absolute.nodeInfo = cls.allInfo.get(cls.nodeType)

		# metaprogramming for fun and profit
		# cmds.select(clear=True)
		return absolute

	def setMObject(cls, obj):
		cls.MObject = obj
		cls.MFnDependency = om.MFnDependencyNode(cls.MObject)
		cls._shapeFn = None
		cls.MDagPath = None
		# check if it's dag or just dependency
		if cls.MObject.hasFn(107):  # MFn.kDagNode
			cls.MDagPath = om.MDagPath.getAPathTo(cls.MObject)
			cls.MFnDagNode = om.MFnDagNode(cls.MObject)
			cls.refreshPath = cls.refreshDagPath
			if cls.MObject.hasFn(110):  # MFnTransform
				cls.MFnTransform = om.MFnTransform(cls.MObject)

		elif cls.MObject.hasFn(4):  # dependency
			cls.refreshPath = cls.returnDepNode

	## refreshing mechanism
	def __str__(self):
		try:
			self.refreshPath()
			if isinstance(self.node, list):
				self.node = self.node[0]
		except:
			self.node = self.MFnDependency.absoluteName()
		return self.node

	"""for repeated operations this will incur a penalty in speed
	consider leaving the call function explicitly to refresh the path"""

	def __repr__(self):
		return self.__str__()

	def __call__(self, *args, **kwargs):
		self.refreshPath()
		return self

	def refreshDagPath(self):
		self.MDagPath = om.MDagPath.getAPathTo(self.MObject)
		#self.node = self.MDagPath.fullPathName()
		self.node = self.MFnDagNode.fullPathName()

	def returnDepNode(self):
		self.node = self.MFnDependency.name()

	def returnBasicNode(self):
		return self.node

	@property
	def name(self):
		return self.node.split("|")[-1]
	@name.setter
	def name(self, value):
		self.MFnDependency.setName(value)

	# i've got no strings, so i have fn

	@property
	def shapeFnType(self):
		# lightweight way to know how to treat the shapeFn
		if self.MObject.hasFn(296): # kMesh
			return "kMesh"
		elif self.MObject.hasFn(267): # kNurbsCurve
			return "kNurbsCurve"
		elif self.MObject.hasFn(294): # kNurbsSurface
			return "kNurbsSurface"
		else:
			return None

	@property
	def shapeFn(self):
		# initialise costly shape mfns only when needed, then never again
		if not self._shapeFn:
			if self.shapeFnType:
				self._shapeFn = eval("om.MFn"+self.shapeFnType[1:]+"(self.MObject)")
			else:
				return self.shape.shapeFn
		return self._shapeFn

	@property
	def isCurve(self):
		return self.shapeFnType == "kNurbsCurve"
	@property
	def isMesh(self):
		return self.shapeFnType == "kMesh"
	@property
	def isSurface(self):
		return self.shapeFnType == "kNurbsSurface"


	@property
	def shape(self):
		"""this feels like a bad idea"""
		if self.isShape():
			return self
		else:
			return AbsoluteNode(shapeFrom(self))

	@property
	def transform(self):
		if self.isTransform():
			return self
		else:
			return AbsoluteNode(tfFrom(self))

	@property
	def parent(self):
		test = cmds.listRelatives(self, parent=True)
		return AbsoluteNode(test[0]) if test else None

	@property
	def children(self):
		test = cmds.listRelatives(self, children=True)
		return [AbsoluteNode(i) for i in test] if test else []

	def parentTo(self, targetParent, *args, **kwargs):
		"""reparents node under target dag"""
		if not self.isDag():
			return
		cmds.parent(self, targetParent, *args, **kwargs)


	def isTransform(self):
		if self.shapeFnType:
			return False
		if self.MDagPath:
			return True
		else:
			return False

	def isShape(self):
		if self.shapeFnType:
			return True

	def isDag(self):
		if self.MObject.hasFn(107): # kDagNode
			return True
		return False

	def hide(self):
		if self.isDag():
			cmds.hide(self)

	def delete(self, full=True):
		"""deletes maya node, and by default deletes entire openmaya framework around it
		tilepile is very unstable, and i think this might be why"""
		self()
		name = self.node
		self.MObject = None
		cmds.delete(name)

	@property
	def nodeType(self):
		"""returns string name of node type - "joint", "transform", etc"""
		return cmds.nodeType(self.node)

	def worldPos(self, asMPoint=True):
		"""returns world position as MPoint"""
		assert self.isDag()
		return om.MPoint(self.MFnTransform.translation(om.MSpace.kWorld))

	@property
	def outWorld(self):
		"""do a procedural thing here to help custom declaration of node info"""
		return self + "." + self.nodeInfo["outWorld"]

	@property
	def outLocal(self):
		return self + "." + self.nodeInfo["outLocal"]

	@property
	def inShape(self):
		return self + "." + self.nodeInfo["inShape"]

	def TRS(self, *args):
		"""returns unrolled transform attrs
		args is any combination of t, r, s, x, y, z
		will return product of each side"""
		mapping = {"T" : "translate", "R" : "rotate", "S" : "scale"}
		if not args:
			args = ["T", "R", "S", "X", "Y", "Z"]
		elif isinstance(args[0], basestring):
			args = [i for i in args[0]]

		args = [i.upper() for i in args]
		attrs = [mapping[i] for i in "TRS" if i in args]
		dims = [i for i in "XYZ" if i in args]

		plugs = []
		for i in attrs:
			for n in dims:
				plugs.append(self+"."+i+n)
		return plugs

	def attrs(self, **kwargs):
		"""return all the attributes of the node"""
		return cmds.listAttr(self(), **kwargs)


	@staticmethod
	def fromMObject(obj):
		"""find node associated with obj and wrap it"""
		name = stringFromMObject(obj)
		return AbsoluteNode(name)

	@staticmethod
	def con(sourcePlug, destPlug):
		"""tribulations"""
		attr.con(sourcePlug, destPlug, f=True)

	def driveWith(self, attrName, driverPlug):
		attr.con(driverPlug, self() + "." + attrName)

	@staticmethod
	def setAttr(plug, value, **kwargs):
		"""set attribute directly"""
		attr.setAttr(plug, value)

	def set(self, attrName, val, **kwargs):
		"""sets value of node's own attr"""
		attr.setAttr(self() + "." + attrName, val, **kwargs)

	def getShapeLayer(self, local=True):
		"""returns live instance of shape"""
		newShape = self.shapeFn.copy()



def ECA(type, name="", colour=None, *args, **kwargs):
	# node = cmds.createNode(type, n=name)
	name = kwargs.get("n") or name
	node = ECN(type, name, *args, **kwargs)
	return AbsoluteNode(node)

#### node wrapper classes ###
class NodeWrapper(AbsoluteNode):
	"""base class for specific wrapper"""

	nodeType = None

	def __new__(cls, name=None):
		"""check"""
		if not cls.nodeType:
			raise NotImplementedError("wrapper {} does not define a node type".format(cls.__name__))
		node = cmds.createNode(cls.nodeType, n=name)
		return super(NodeWrapper, cls).__new__(node)


class RemapValue(NodeWrapper):
	"""wrapper for rempValue nds"""
	nodeType = "remapValue"

	def getRampInstance(self, name="rampInstance"):
		"""creates new ramp exactly mirroring master and connects it by message"""
		newRemap = ECA("remapValue", n=name)
		for i in range(cmds.getAttr(self+".value", size=True)):
			attr.con(self+".value[{}]".format(i),
			         newRemap+".value[{}]".format(i))
		attr.makeMutualConnection(self, newRemap, attrType="message",
		                          startName="instances", endName="master")
		return newRemap

	@property
	def instances(self):
		"""look up ramps connected to master by string"""
		return attr.getImmediateFuture(self+".instances")



