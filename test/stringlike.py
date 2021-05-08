

from maya import cmds
from maya.api import OpenMaya as om

import abc, inspect
import types, ctypes
from six import iteritems, with_metaclass, string_types
import collections
from functools import wraps


def getMObject(node):
	sel = om.MSelectionList()
	sel.add(str(node)) # one option
	sel.add(node)
	return sel.getDependNode(0)


class StringLikeSimple(object):
	""" This is enough for cmds, but
	fails at om calls
	It's also fundamentally not a string
	"""

	def __init__(self, base="_default"):
		self._inner = str(base)
		# self.__class__ = str

	def __repr__(self):
		return self.__str__()
	def __str__(self):
		return str(self._inner)

	# def __class__(self):
	# 	return str


def testSimple():
	cmds.file(new=1, f=1)

	obj = StringLikeSimple()
	obj._inner = "newInner"

	# maya section
	c = cmds.polyCube()[0]
	obj._inner = c

	cmds.warning(obj)
	cmds.warning(obj._inner)
	print(obj)
	result = cmds.rename(obj, "intermediatePoly")
	obj._inner = result

	newResult = cmds.rename(obj, "successfulRename")
	obj._inner = newResult

	dObj = StringLikeSimple()
	dObj._inner = cmds.duplicate(obj, n="duplicatePoly")[0]

	cmds.parent(dObj, obj)
	cmds.warning(dObj)
	dObj._inner = cmds.rename(dObj, "childDuplicatePoly")
	print(cmds.listRelatives(dObj, allParents=1))

	cmds.parent(dObj, world=1)
	cmds.parent(obj, dObj)
	# all seems to work

	# # fails at the openmaya stage
	dMObj = getMObject(dObj)
	bMObj = getMObject(obj)



class StringLikeMeta(type):

	def __call__(self, *args, **kwargs):
		print("meta __call__", args, kwargs)
		return super(StringLikeMeta, self).__call__(*args, **kwargs)


class StringMix(object):
	""" this is getting weird """

class StringLikeFull(str):
	"""
	attempted to return user object from new / call :
	'string in type only'
	as far as maya is concerned, it didn't work
	"""

	@staticmethod
	def __new__(S, *more):
		print("str __new__", S, more)
		return str.__new__(S, *more)
		# return type.__new__(S) # user class is not subtype of type
		# return object.__new__(S, *more) # 'not safe' ok mum
		#return object.__new__(StringMix)
		#  returns literally a different object - not useful

	def __init__(self, value=""):
		print("str __init__", value)
		self._inner = value

	@property
	def value(self):
		return self._inner
	@value.setter
	def value(self, value):
		self._inner = value

	def __class__(self):
		return str

	def __str__(self):
		print("str __str__ called")
		val = str(self._inner)
		print("returning", val)
		return val
	def __repr__(self):
		print("str __repr__ called")
		return self.__str__()

def testComplex():

	cmds.file(new=1, f=1)
	poly = cmds.polyCube()[0]

	obj = StringLikeFull(poly)
	print("type", type(obj))
	cmds.warning(obj)
	bMObj = getMObject(obj)

	obj.value = "NEW VALUE"
	cmds.warning(obj) # does not update
	# obj still associated with its previous value
	print("obj", obj) # of course actual python calls work fine

	result = cmds.rename(obj, "newPolyName")
	obj.value = result
	bMObj = getMObject(obj) # fails

# either replace references to string object in memory?
# or patch om modules directly somehow?
# OR
# when __str__ is called, move the address of the entire object
# to that of the new string? bit mental

"""Try the patching system - recursively patch every callable
in OpenMaya to collapse objects of specific class to their string
representation.
yeah it sounds silly to me too"""
def patchFn(fn):
	""" reversible patch function
	returns original for later restoration"""
	def _str(var): # macro to patch var types
		return str(var) if isinstance(var, StringLikeSimple) else var

	@wraps(fn)
	def _wrapper(*args, **kwargs):
		newArgs = [_str(i) for i in args]
		newKwargs = {_str(k) : _str(v) for k, v in iteritems(kwargs)}
		result = fn(*newArgs, **newKwargs)
		return result
	return _wrapper, fn

def patchObj(obj):
	""" patch all function members of an object with patchFn()
	to collapse StringLikeSimple to actual strings """
	for k, v in inspect.getmembers(obj):
		if callable(v):
			val, oldVal = patchFn(v)
			obj.__dict__[k] = val
		else:
			patchObj(v)

def test():
	testSimple()
	testComplex()
	# couldn't get this to work
	# patchObj(om.MSelectionList)
	pass

