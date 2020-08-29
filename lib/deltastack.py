
import copy
from collections import OrderedDict
import inspect


from edRig.lib.python import AbstractTree, debug

""" so it turns out this is really hard """

""" live inheritance is achieved by passing out a proxy object wrapper,
and repeatedly regenerating proxy object data, 
while comparing to given base object

2 problems must be solved:
 - how do we deal with complex and deep objects
 - how do we make a mask of a mask
"""


class CallWrapper(object):
	""" pseudo-decorator
	for pre- and post-call wrapping of specific function """
	def __init__(self, fn, *args, **kwargs):
		self._fn = fn

	def preCall(self, *args, **kwargs):
		pass
	def postCall(self, result, *args, **kwargs):
		pass

	def __call__(self, *args, **kwargs):
		self.preCall(*args, **kwargs)
		result = self._fn(*args, **kwargs)
		self.postCall(result, *args, **kwargs)
		return result


class Proxy(object):
	""" Transparent proxy for most objects
	code recipe 496741
	further modifications from ya boi """
	#__slots__ = ["_obj", "__weakref__"]
	_class_proxy_cache = {} # { class : { class cache } }
	_proxyAttrs = ("_proxyObjRef", "_proxyObj")
	_proxyObjKey = "_proxyObjRef" # attribute pointing to object
	_methodHooks = {}

	def __init__(self, obj):
		#object.__setattr__(self, self._proxyObjKey, obj)
		self._proxyObj = obj

	@property
	def _proxyObj(self):
		return self._returnProxy()
	@_proxyObj.setter
	def _proxyObj(self, val):
		object.__setattr__(self, self._proxyObjKey, val)

	def _returnProxy(self):
		""" hook for extending proxy behaviour
		prefer overriding this over properties"""
		return object.__getattribute__(self, self._proxyObjKey)

	# proxying (special cases)
	def __getattribute__(self, name):
		try: # look up attribute on proxy class first
			return object.__getattribute__(self, name)
		except:
			return getattr( self._proxyObj, name)

	def __delattr__(self, name):
		delattr(object.__getattribute__(self, self._proxyObjKey), name)

	def __setattr__(self, name, value):
		if name in self.__class__._proxyAttrs:
			object.__setattr__(self, name, value)
		else:
			setattr(object.__getattribute__(self, self._proxyObjKey), name, value)
			setattr(self._proxyObj, name, value)

	def __nonzero__(self):
		return bool(object.__getattribute__(self, self._proxyObjKey))
		return bool(self._proxyObj)

	def __str__(self):
		return str(object.__getattribute__(self, self._proxyObjKey))

	def __repr__(self):
		return repr(object.__getattribute__(self, self._proxyObjKey))

	# factories
	_special_names = [
		'__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__',
		'__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__',
		'__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__',
		'__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
		'__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__',
		'__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__',
		'__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__',
		'__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__',
		'__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__',
		'__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__',
		'__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__',
		'__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__',
		'__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__',
		'__truediv__', '__xor__', 'next',
	]

	@classmethod
	def _create_class_proxy(cls, theclass):
		"""creates a proxy for the given class"""
		# combine declared proxy attributes
		cls._proxyAttrs = set(cls._proxyAttrs)
		for base in cls.__mro__:
			if base == object: break
			cls._proxyAttrs.update(base._proxyAttrs)

		def make_method(name):
			def method(self, *args, **kw):
				return getattr(
					self._proxyObj,
					name)(*args, **kw)
			return method

		namespace = {}
		for name in cls._special_names:
			if hasattr(theclass, name):
				namespace[name] = make_method(name)
		return type("{}({})".format(cls.__name__, theclass.__name__),
		            (cls,), namespace)

	def __new__(cls, obj, *args, **kwargs):
		"""
        creates a proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        base Proxy class holds master dict
        """
		# looks up type-specific proxy class
		cache = Proxy.__dict__["_class_proxy_cache"]
		try:
			genClass = cache[cls][type(obj)]
		except KeyError:
			genClass = cls._create_class_proxy(type(obj))
			cache[cls] = { type(obj) : genClass }

		# create new proxy instance with type-specific proxy class
		ins = object.__new__(genClass)

		# run init on created instance
		genClass.__init__(ins, obj, *args, **kwargs)
		return ins


class Delta(Proxy):
	""" delta-tracking wrapper
	also adapted from 496741 """

	_proxyAttrs = (#"_proxyObjRef", "_proxyObj",
	               "_baseObj", "_mask")

	def __init__(self, obj):
		self._baseObj = obj # reference to base object to draw from
		self._proxyObj = copy.copy(obj)
		self._mask = { "added" : {}, "modified" : {}, "removed" : {} }
		self.extractMask(self._baseObj, self._proxyObjRef)

	def _returnProxy(self):
		""" runs mask operation every time proxy is accessed
		never said this would be fast """
		return super(Delta, self)._returnProxy()


	def extractMask(self, baseObj=None, deltaObj=None):
		""" compares proxy object to base, collates delta to mask """
	def applyMask(self, newObj=None):
		""" applies delta mask to product object """

	def product(self):
		self.extractMask(self._baseObj, self._proxyObjRef)
		newObj = copy.copy(self._baseObj)
		self.applyMask(newObj)
		return newObj

	def serialise(self):
		pass

	@classmethod
	def deserialise(cls, data, baseObj):
		""" loads delta object from dict and reapplies to baseObj """
		pass


class DictDelta(Delta):
	def extractMask(self, proxyObj=None):
		self._mask["added"] = {
			pK : pV for pK, pV in self._proxyObj.iteritems() if \
				pK not in self._baseObj }
		self._mask["modified"] = {
			pK : pV for pK, pV in self._proxyObj.iteritems() if \
				self._baseObj.get(pK) != pV }
		# added and modified functionally the same here

	def applyMask(self, newObj=None):
		self._proxyObj.update(self._mask["added"])
		self._proxyObj.update(self._mask["modified"])

class ListDelta(Delta):
	""" basic, indices not working """
	def extractMask(self):
		self._mask["added"] = {
			self._proxyObj.index(i) : i for i in self._proxyObj \
				if not i in self._baseObj }
	def applyMask(self, newObj=None):
		for index, val in self._mask["added"]:
			try:
				self._proxyObj.insert(index, val)
			except:
				self._proxyObj.append(val)

class TreeDelta(Delta):
	""" final boss """

	def __init__(self, obj):
		""" a mask initialised on a tree then create
		masks all the way down? probably
		"""
		super(TreeDelta, self).__init__(obj)
		for branch in obj.branches:
			""" vulnerable to name changing, need proper hashing for
			branch objects """
			self._mask["modified"][branch.name] = branch


	def extractMask(self, baseObj=None, deltaObj=None):
		""" avoid looking up instance attributes here
		this should probably be static """
		# added trees are easiest, no child deltas needed
		self._mask["added"] = {
			branch.index : branch for branch in baseObj.branches \
				if not branch.name in baseObj._map
		} # need better index integration
		# store indices separately? idk
		self._mask["modified"] = { # modified is list of child masks
		}
		""" modifications have no hierarchy in deltamask,
		mask should only track value and added and removed branches
		otherwise lookup tree objects and create new delta objects?
		but then how the hell do you serialise and deserialise """


		if deltaObj.value != baseObj.value:
			self._mask["value"] = deltaObj.value
		else: self._mask["value"] = None


	def applyMask(self, newObj=None):
		for index, branch in self._mask["added"]:
			newObj.addChild(branch, index)
		if self._mask.get("value") is not None:
			newObj.value = self._mask["value"]

	def serialise(self):
		data = {
			"added" : {},
			"value" : self._mask["value"]
		}
		for index, branch in self._mask["added"]:
			data["added"][index] = branch.serialise()

	@classmethod
	def deserialise(cls, data, baseObj):
		""" setting redundant values on proxy is fine as
		extractMask() will remove them anyway """
		proxy = cls(baseObj)
		for index, branchData in data["added"]:
			branch = AbstractTree.fromDict(branchData)
			proxy.addChild(branch, index=index)

		proxy.value = data["value"]






"""
# toughest scenario:
baseObj
proxy = Delta(baseObj)
proxy["key"] = valueA
baseObj["key"] = valueB

"""
# test for interfaces with the tree structure
testTree = AbstractTree("TestRoot")
testTree("asdf").value = "firstKey"
testTree("parent").value = "nonas"
testTree("parent.childA").value = 930
testTree("parent.childA").extras["options"] = (930, "eyyy")
testTree("parent.childB").value = True

# cannot do nested list inputs yet
testTree["parent.listEntry"] = "[eyyy, test, 4.3, '', 2e-10, False]"
testTree["parent.nestedList"] = "[eyyy, test, 4.3, '', [4e4, i, 33, True], 2e-10]"




if __name__ == '__main__':

	debug(testTree)
	proxyTree = TreeDelta(testTree)

	proxyTree["proxyKey"] = "w e w _ l a d"

	print(proxyTree.display())



	baseDict = {"baseKey" : 69,
	            "baseKeyB" : "eyy"}
	debug(baseDict)

	replaceDict = {"replacedDict" : 3e4}

	# testDict = Proxy(baseDict)
	# testDict["proxyTest"] = True
	# debug(testDict)
	# testDict._proxyObj = replaceDict
	# debug(testDict)
	#
	# proxyDict = Delta(baseDict)
	# debug(proxyDict)
	#
	# baseDict["newBaseKey"] = 49494
	# debug(proxyDict)
	#
	# proxyDict["newProxyKey"] = "FAJLS"
	# print("baseDict is {}".format(baseDict))
	# debug(proxyDict)



