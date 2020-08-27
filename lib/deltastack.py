
import copy
from collections import OrderedDict


from edRig.lib.python import AbstractTree, debug

""" so it turns out this is really hard """

""" live inheritance is achieved by passing out a proxy object wrapper,
and repeatedly regenerating proxy object data, 
while comparing to given base object

2 problems must be solved:
 - how do we deal with complex and deep objects
 - how do we make a mask of a mask
"""


def isSimple(obj):
	return isinstance(obj, (basestring, tuple, int, float, bool, None))



class Proxy(object):
	""" Transparent proxy for most objects
	code recipe 496741
	further modifications from ya boi """
	#__slots__ = ["_obj", "__weakref__"]
	_class_proxy_cache = {} # { class : { class cache } }
	_proxyAttrs = ("_proxyObj", )
	_proxyObjKey = "_proxyObj" # attribute pointing to object

	def __init__(self, obj):
		object.__setattr__(self, self._proxyObjKey, obj)

	# proxying (special cases)
	def __getattribute__(self, name):
		try: # look up attribute on proxy class first
			return object.__getattribute__(self, name)
		except:
			return getattr(object.__getattribute__(
				self, self._proxyObjKey), name)

	def __delattr__(self, name):
		delattr(object.__getattribute__(self, self._proxyObjKey), name)

	def __setattr__(self, name, value):
		if name in self.__class__._proxyAttrs:
			object.__setattr__(self, name, value)
		else:
			setattr(object.__getattribute__(self, self._proxyObjKey), name, value)

	def __nonzero__(self):
		return bool(object.__getattribute__(self, self._proxyObjKey))

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

		def make_method(name):
			def method(self, *args, **kw):
				# insert live object lookup here
				return getattr(
					object.__getattribute__(self, cls._proxyObjKey),
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
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
		# looks up type-specific proxy class
		cache = Proxy.__dict__["_class_proxy_cache"]
		try:
			genClass = cache[cls][type(obj)]
		except KeyError:
			genClass = cls._create_class_proxy(type(obj))
			#cache[cls] = {obj.__class__ : theclass}
			cache[cls] = { type(obj) : genClass }

		# create new proxy instance with type-specific
		# proxy class
		ins = object.__new__(genClass)

		# run init on created instance
		genClass.__init__(ins, obj, *args, **kwargs)
		return ins



class Delta(Proxy):
	""" delta-tracking wrapper
	also adapted from 496741 """

	_proxyAttrs = ("_baseObj", "_proxyObj", "_mask")

	def __init__(self, obj):
		self._baseObj = obj # reference to base object to draw from
		self._proxyObj = copy.copy(obj)
		self._mask = { "added" : {}, "modified" : {} }
		self.extractMask()

	def extractMask(self):
		""" compares proxy object to base, collates delta to mask """
	def applyMask(self):
		""" applies delta mask to product object """

	def product(self):
		self.extractMask()
		self._proxyObj = copy.copy(self._baseObj)
		self.applyMask()
		return self

	def serialise(self):
		pass

	@classmethod
	def deserialise(cls, data, baseObj):
		""" loads delta object from dict and reapplies to baseObj """
		pass


class DictDelta(Delta):
	def extractMask(self):
		self._mask["added"] = {
			pK : pV for pK, pV in self._proxyObj.iteritems() if \
				pK not in self._baseObj }
		self._mask["modified"] = {
			pK : pV for pK, pV in self._proxyObj.iteritems() if \
				self._baseObj.get(pK) != pV }
		# added and modified functionally the same here

	def applyMask(self):
		self._proxyObj.update(self._mask["added"])
		self._proxyObj.update(self._mask["modified"])

class ListDelta(Delta):
	""" basic, indices not working """
	def extractMask(self):
		self._mask["added"] = {
			self._proxyObj.index(i) : i for i in self._proxyObj \
				if not i in self._baseObj }
	def applyMask(self):
		for index, val in self._mask["added"]:
			try:
				self._proxyObj.insert(index, val)
			except:
				self._proxyObj.append(val)

class TreeDelta(Delta):
	""" final boss
	deep trees even more difficult, as copying doesn't work
	need to keep consistent objects throughout operations"""
	def extractMask(self):
		# added trees are easiest, no child deltas needed
		self._mask["added"] = {
			branch.index : branch for branch in self._baseObj.branches \
				if not branch.name in self._baseObj._map
		} # need better index integration
		self._mask["modified"] = { # modified branches get new masks?
		}

		if self._proxyObj.value != self._baseObj.value:
			self._mask["value"] = self._proxyObj.value
		else: self._mask["value"] = None


	def applyMask(self):
		for index, branch in self._mask["added"]:
			self._proxyObj
		if self._mask.get("value") is not None:
			self._proxyObj.value = self._mask["value"]

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



	baseDict = {"baseKey" : 69,
	            "baseKeyB" : "eyy"}
	debug(baseDict)

	replaceDict = {"replacedDict" : 3e4}

	testDict = Proxy(baseDict)
	testDict["proxyTest"] = True
	debug(testDict)
	testDict._proxyObj = replaceDict
	debug(testDict)

	proxyDict = Delta(baseDict)
	debug(proxyDict)

	baseDict["newBaseKey"] = 49494
	debug(proxyDict)

	proxyDict["newProxyKey"] = "FAJLS"
	print("baseDict is {}".format(baseDict))
	debug(proxyDict)



