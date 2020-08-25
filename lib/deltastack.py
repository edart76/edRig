
import copy
from collections import OrderedDict


from edRig.lib.python import AbstractTree, debug

""" so it turns out this is really hard """

""" I see two methods to achieve this 'live inheritance' effect: 
until now I've approached the DeltaMask as a constant interface and wrapper,
accounting for and special-casing all instance methods, magic methods, etc

alternatively, consider restricting to applying and regenerating the mask,
and passing out a reference to it?
but it has to be a reference to self or it will surely get destroyed when result is regenerated

3 problems must be solved:
 - how do we actually get the thing to work
 - how do we serialise it
 - how do we make a mask of a mask
"""


def isSimple(obj):
	return isinstance(obj, (basestring, tuple, int, float, bool, None))



class Proxy(object):
	""" Transparent proxy for most objects
	code recipe 496741
	further modifications from ya boi """
	#__slots__ = ["_obj", "__weakref__"]
	_class_proxy_cache = {}
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
		return type("{}({})".format(cls.__name__, theclass.__name__), (cls,), namespace)

	def __new__(cls, obj, *args, **kwargs):
		"""
        creates a proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
		# looks up type-specific proxy class
		#try:
		cache = cls.__dict__["_class_proxy_cache"]
		# except KeyError:
		# 	cls._class_proxy_cache = cache = {}
		try:
			theclass = cache[obj.__class__]
		except KeyError:
			cache[obj.__class__] = theclass = cls._create_class_proxy(obj.__class__)

		# the above can be skipped with concrete subclasses

		# create new proxy instance with type-specific
		# proxy class
		ins = object.__new__(theclass)

		# run init on created instance
		theclass.__init__(ins, obj, *args, **kwargs)
		return ins



class Delta(Proxy):
	""" delta-tracking wrapper
	also adapted from 496741 """
	_class_proxy_cache = {} # will likely need specific classes anyway

	_proxyAttrs = ("_baseObj", "_proxyObj", "_mask")

	def __init__(self, obj):
		self._baseObj = obj # reference to base object to draw from
		self._proxyObj = copy.copy(obj)
		self._mask = {}
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




if __name__ == '__main__':
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


class DeltaMask(Proxy):


	def setObject(self, obj):
		""" mask can be assigned to any object asynchronously """
		self._baseObj = obj

	def setMask(self, maskDict):
		self._mask = maskDict


	def result(self):
		if self._productObj:
			self.extractMask()
		# update with shallow copy of base object
		self._productObj = copy.copy(self._baseObj)
		self.applyMask()
		self.wrapProduct()
		return self


	def extractMask(self):
		pass
	def applyMask(self):
		pass
	def wrapProduct(self):
		""" updates this proxy to point to a new object
		references to this mask object will
		always be valid """


	def collapse(self):
		""" flatten delta mask to entirely new object """
		pass



	# saving and loading
	def serialise(self):
		""" no reference to object """
		return self._mask

	@classmethod
	def fromDict(cls, data):
		deltaMask = cls()
		deltaMask.setMask(data)


class ListDelta(DeltaMask):
	""" at some point maybe refit this to abstractTree as well"""
	OBJ_CLASS = list

	def absIndex(self, index):
		""" converts negative list index to positive value """
		if index < 0:
			return len(self._obj) + index
		return index
	
	def result(self):
		length = max( max(self.map.keys()), len(self._obj))
		newObj = list(self._obj) + [None] * ( length - len(self._obj) )
		for k, v in self._mask.iteritems():
			newObj[k] = v
		return newObj



class AbstractTreeDelta(DeltaMask):
	""" if values are modified, use primitive type masks
	if new branches are added, create new abstractTrees, not masks
	trigger warning: code duplication """
	OBJ_CLASS = AbstractTree

	def __init__(self, obj=None):
		super(AbstractTreeDelta, self).__init__(obj)
		self._mask = {
			"value" : None, # raw data or deltamask
		}

	def __call__(self, address):
		""" wrapping base tree lookup"""

	pass




class DictDelta(DeltaMask):
	OBJ_CLASS = dict

	def transformed(self):
		"""construct a new dict for return, don't try to
		frankenstein the same bound object
		all other dict methods are overridden anyway
		:rtype dict"""

		tfData = { k : v for k, v in self.obj.iteritems()}
		for i in self.mask["removed"]:
			tfData.pop(i)
		for k, v in self.mask["added"].iteritems():
			tfData[k] = v
		for k, v in self.mask["modified"].iteritems():
			tfData[k] = v
		""" here addition and modification are the same - 
		is that true everywhere? """
		return tfData


		pass

	@property
	def obj(self):
		""":rtype dict"""
		return super(DictDelta, self).obj or {}



class OrderedDictDelta(DictDelta):
	OBJ_CLASS = OrderedDict
	pass


DELTA_CLASSES = {
	list : ListDelta,
	dict : DictDelta,
	AbstractTree : AbstractTreeDelta,
	OrderedDict : OrderedDictDelta
}


"""test case let's go


class Test(object):
	
	def __init__:
		self.A = 5
		self.B = "this is test"
		
newTest = Test()
stack = DeltaStack.trackObject(newTest)

- this will return a deltaStack with newTest as its base
this will be a top-level wrapper around newTest - any modification 
of stack's attributes will be a modification delta

eg

stack.C = "newAttr"
is an object-level modification, comprised of an attribute-level addition

does not add the attribute to stack. compares previous transformedState of stack -
this is treated as a dict for sanity - see if it contains C.

if it does, then object level is NOT MODIFIED - no object level delta is created
attribute lookup ten returns an inner stack, which handles it further.

if it doesn't, an addition delta is created at object level to add the attribute
AS NEW STACK with base state None - 
object level contains no knowledge of attribute's value

for convenience, register attribute value as stack base state. don't think it
matters, but helps for determining delta type etc

new stack processes attribute value, creates child stacks if necessary
(if need to tokenise string, etc)




is it worth returning a new deltastack around this attribute, as it has
 no base state? would only allow for undo operations
 
stack.B = "this is new test"
more interesting.

compare the source state and the target state

is it worth tracking from the top down like this? surely bottom up would
make more sense





accessing object must apply all relevant modifications

















"""

