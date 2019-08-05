"""AbsoluteNode and object-style nod wrappers"""
import weakref, ctypes

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
#class AbsoluteNode(object):

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

	defaultAttrs = {}
	# override with {"nodeState" : 1} etc

	_isDag = False

	def __new__(cls, node, ):
		"""nota bene: strings are immutable. thus to update the
		string value of absoluteNode, we must return a NEW
		AbsoluteNode every time it changes
		no that's dumb"""
		# this is the stripped down fast version of pymel

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
			#absolute.refreshPath = absolute.returnBasicNode
			return absolute
		obj = MObjectFrom(node)
		absolute.setMObject(obj)

		absolute._shape = None
		absolute._transform = None

		# metaprogramming for fun and profit
		# cmds.select(clear=True)

		# callbacks attached to node, to delete on node deletion
		absolute.callbacks = []

		return absolute

	def setMObject(cls, obj):
		cls.MObject = obj # not weakref-able :(
		cls.MFnDependency = om.MFnDependencyNode(cls.MObject)
		cls._shapeFn = None
		cls.MDagPath = None
		# check if it's dag or just dependency
		if cls.MObject.hasFn(107):  # MFn.kDagNode
			#print "assigning dag node"
			cls._isDag = True
			cls.MDagPath = om.MDagPath.getAPathTo(cls.MObject)
			cls.MFnDagNode = om.MFnDagNode(cls.MObject)
			#cls.refreshPath = cls.refreshDagPath
			if cls.MObject.hasFn(110):  # MFnTransform
				cls.MFnTransform = om.MFnTransform(cls.MObject)

		elif cls.MObject.hasFn(4):  # dependency
			#print "assigning basic node"
			#cls.refreshPath = cls.returnDepNode
			pass

	def refreshPath(self):
		if self._isDag:
			return self.refreshDagPath()
		else:
			return self.returnDepNode()

	## refreshing mechanism
	def __str__(self):
		try:
			self.refreshPath()
			if isinstance(self.node, list):
				self.node = self.node[0]
		except:
			print "refreshPath encountered error"
			self.node = self.MFnDependency.absoluteName()
		#print "str self "+self.node
		return str.__new__(str, self.node)

	"""for repeated operations this will incur a penalty in speed
	consider leaving the call function explicitly to refresh the path"""

	def __repr__(self):
		"""never called apparently"""
		name = self.__str__()
		print "repr self " + name
		return name

	def __call__(self, *args, **kwargs):
		self.refreshPath()
		return str(self)

	"""self object not behaving as it should
	need to return this AbsoluteNode instance, while still having the 
	string value of the new name"""

	def __add__(self, other):
		return self() + other
	def __iadd__(self, other):
		return self() + other
	def __len__(self):
		return len( self() )
	def __getitem__(self, item):
		return self().__getitem__(i)


	def refreshDagPath(self):
		#self.MDagPath = om.MDagPath.getAPathTo(self.MObject)
		self.node = self.MFnDagNode.fullPathName()
		return self.node

	def returnDepNode(self):
		self.node = self.MFnDependency.name()
		return self.node

	def returnBasicNode(self):
		return self.node

	@property
	def name(self):
		return self.node.split("|")[-1]
	@name.setter
	def name(self, value):
		self.MFnDependency.setName(value)
		#cmds.rename(self(), value)
		self()

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
			return self()
		elif not self._shape:
			self._shape = AbsoluteNode( shapeFrom( self() ) )
		return self._shape

	@property
	def transform(self):
		if self.isTransform():
			return self()
		elif not self._transform:
			self._transform = AbsoluteNode( tfFrom( self() ) )
		return self._transform

	@property
	def parent(self):
		"""replace with api call"""
		test = cmds.listRelatives(self, parent=True)
		return AbsoluteNode(test[0]) if test else None

	@property
	def children(self):
		test = cmds.listRelatives(self, children=True)
		return [AbsoluteNode(i) for i in test] if test else []

	def parentTo(self, targetParent, *args, **kwargs):
		"""reparents node under target dag
		replace with api call"""
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
		tesserae is very unstable, and i think this might be why"""
		self()
		name = self.node
		self.MObject = None
		cmds.delete(name)

	#@property
	# @classmethod
	def nodeType(self):
		"""returns string name of node type - "joint", "transform", etc"""
		return cmds.nodeType(self.node)

	def worldPos(self, asMPoint=True):
		"""returns world position as MPoint"""
		assert self.isDag()
		return om.MPoint(self.MFnTransform.translation(om.MSpace.kWorld))

	@property
	def nodeInfo(self):
		"""return specific info for node class"""
		# this should be overwritten by specific subclasses
		return self.allInfo[self.nodeType()]

	@property
	def outWorld(self):
		"""do a procedural thing here to help custom declaration of node info"""
		return self() + "." + self.nodeInfo.get("outWorld")

	@property
	def outLocal(self):
		return self() + "." + self.nodeInfo.get("outLocal")

	@property
	def inShape(self):
		#print "inShape self {}".format(self)
		#print "inshape nodeInfo {}".format(self.nodeInfo)
		plug = "{}.{}".format(self, self.nodeInfo.get("inShape") )
		#print "inShape plug {}".format(plug)
		return plug

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

	@staticmethod
	def conOrSet(a, b, f=True):
		"""tribulations"""
		attr.conOrSet(a, b, f)

	def driveWith(self, attrName, driverPlug):
		attr.con(driverPlug, self() + "." + attrName)

	@staticmethod
	def setAttr(plug, value, **kwargs):
		"""set attribute directly"""
		attr.setAttr(plug, value)

	def set(self, attrName=None, val=None, multi=None, **kwargs):
		"""sets value of node's own attr
		REFACTOR to catalogue MPlugs and set them directly"""
		if isinstance(multi, dict):
			attr.setAttrsFromDict(multi, node=self())
		else:
			attr.setAttr(self() + "." + attrName, val, **kwargs)

	def getMPlug(self, plugName):
		"""return MPlug object"""
		if plugName not in self.attrs():
			raise RuntimeError("plug {} not found in attrs {}".format(
				plugName, self.attrs() ) )
		return self.MFnDependency.findPlug(plugName, False)

	def getShapeLayer(self, name="newLayer", local=True, newTf=True):
		"""returns live instance of shape
		should probably not live in our master object of everything"""
		parent = ECA("transform", n=name) if newTf else \
			self.transform.MObject
		parentObj = parent.MObject
		newShape = self.shapeFn.copy(self.MObject, parentObj)
		newNode = AbsoluteNode.fromMObject(newShape)
		newNode.name = name+"Shape"

		print "new {}, {}".format(newNode, newNode.inShape)

		self.con(self.outLocal, newNode.inShape)
		print "shadingEngine {}".format(self.shadingEngine)
		newNode.connectToShader(self.shadingEngine)
		return newNode

	def connectToShader(self, shader):
		"""takes shadingEngine and connects shape"""
		self.con(self+".instObjGroups[0]", shader+".dagSetMembers")

	@property
	def shadingEngine(self):
		"""returns connected shadingEngine node"""
		if self.isShape():
			return attr.getImmediateFuture(self+".instObjGroups[0]")[0]

	@classmethod
	def create(cls, name=None, n=None, *args, **kwargs):
		"""any subsequent wrapper class will create its own node type"""
		# nodeTypeStr = cls.nodeType() or cls.__name__
		nodeTypeStr = cls.__name__
		nodeType = nodeTypeStr[0].lower() + nodeTypeStr[1:]
		name = name or n or "eyy"
		node = cls(cmds.createNode(nodeType, n=name)) # cheeky
		return node

	def setDefaults(self):
		"""called when node is created"""
		if self.defaultAttrs:
			attr.setAttrsFromDict(self.defaultAttrs, self)

	def copy(self, name=None):
		"""copies node, without copying children"""
		name = name or self.name+"_copy"
		node = AbsoluteNode(cmds.duplicate(self(), parentOnly=True, n=name)[0])
		if self.isShape():
			cmds.parent(node, self.parent, r=True, s=True)
		elif self.isDag():
			cmds.parent(node, self.parent)
		return node


def ECA(type, name="", colour=None, *args, **kwargs):
	# node = cmds.createNode(type, n=name)
	name = kwargs.get("n") or name
	node = ECN(type, name, *args, **kwargs)
	return AbsoluteNode(node)


class PlugObject(str):
	"""small wrapper allowing plug to be returned as priority,
	and while still accessing the node easily
	NOT robust to name changes"""

	def __new__(cls, plug):
		plugObj = str.__new__(plug)
		plugObj.plug = plug

	def __repr__(self):
		return self.plug
	def __str__(self):
		return self.__repr__()

	@property
	def node(self):
		return self.getNode()
	def getNode(self):
		return ".".join(self.split(".")[1:])

	@property
	def MPlug(self):
		"""shrug"""
		pass



class RemapValue(AbsoluteNode):
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



