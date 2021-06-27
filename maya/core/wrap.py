"""Module for wrapping cmds at startup,
and holding conversion decorators to show which functions
accept which types

also patches __getattribute__ on cmds module, so that
cmds functions are monkeypatched lazily on lookup
"""
from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
from functools import partial, wraps
import builtins

import inspect
import traceback

from edRig import cmds, om

# import the node base / mixin for instance checking
from edRig.maya.core.bases import NodeBase

# allow weakrefs to MObjects by overriding __slots__
def patchMObjectWeakrefs():
	# om.MObject.__slots__ = tuple(list(om.MObject.__slots__)
	#                              + ["__weakref__"])
	pass


def returnList(wrapFn):
	@wraps(wrapFn)
	def _innerFn(*args, **kwargs):
		result = wrapFn(*args, **kwargs)
		if result is None:
			print("returned None, changing to list")
			return []
		return result

	return _innerFn


listFunctions = ["ls", "listRelatives", "listHistory", "listConnections",
	                 "listAttr"]

def wrapListFns():
	# patch maya cmds "list-" functions to return lists no matter what
	for fnName in listFunctions:
		try:
			fn = getattr(cmds, fnName)
			# check if has already run
			base = getattr(cmds, "_" + fnName, None)
			if base:
				setattr(cmds, fnName, returnList(base))
			else:
				# set original function to "_fnName"
				setattr(cmds, "_" + fnName, fn)
				# update module refrence with wrapped
				setattr(cmds, fnName, returnList(fn))

		except:
			print(("error wrapping {}".format(fnName)))
			print((traceback.format_exc()))

def typeSwitchInPlace(obj, typeMap:Dict[type, type], copy=False):
	"""given arbitrary prim structure, either return flat converted object
	or replace objects in place"""

	if isinstance(obj, (tuple, list, set)):
		newData = [typeSwitchInPlace(i, typeMap) for i in obj]
		return type(obj)(newData)
	elif isinstance(obj, (dict, )):
		newKeys = [typeSwitchInPlace(i, typeMap)
		           for i in obj.keys()]
		newValues = [typeSwitchInPlace(i, typeMap)
		             for i in obj.values()]
		return {k : v for k, v in zip(newKeys, newValues)}

	# is singular object, convert
	# basic iteration here, we don't expect hugely rich type mappings on functions
	for srcType, dstType in typeMap.items():
		if isinstance(obj, srcType): # take first match
			# we assume a simple initialiser is enough to convert
			# if not we have problems

			try:
				return dstType(obj)
			except:
				print("direct conversion encountered issue with",
				      obj, type(obj))
				continue
	return obj

# list of all types that could be converted
nodeTypes = [NodeBase, str]

# decorator to functions
def nodeType(toType:type=None):
	"""define what type nodes should be converted to"""
	typeMap = {i : toType for i in nodeTypes}
	def deco(fn:function):
		#@wraps(fn)
		def wrapper(*fnArgs, **fnKwargs):
			"""convert argument types"""
			fnArgs = typeSwitchInPlace(fnArgs, typeMap)
			fnKwargs = typeSwitchInPlace(fnKwargs, typeMap)
			result = fn(*fnArgs, **fnKwargs)
			return result
		#wrapper.__name__ = fn.__name__
		return wrapper
	return deco

# actual function to wrap arbitrary functinos
def typeSwitchParamsPatch(fn, typeMap):
	#@wraps(fn)
	def wrapper(*fnArgs, **fnKwargs):
		"""convert argument types"""
		newArgs = typeSwitchInPlace(fnArgs, typeMap)
		newKwargs = typeSwitchInPlace(fnKwargs, typeMap)
		#try:
		result = fn(*newArgs, **newKwargs)
		return result
		# except Exception as e:
		# 	print(fnArgs)
		# 	print(newArgs)
		# 	raise e

	#wrapper.__name__ = fn.__name__
	return wrapper

def wrapCmdFn(fn):
	"""wrap single cmd to flatten NodeBases (AbsoluteNodes)
	to strings when passed as params"""
	print("wrapping cmd", fn.__name__)
	typeMap = {NodeBase : str} # can add entries for pm nodes, cmdx etc
	fn = typeSwitchParamsPatch(fn, typeMap)
	return fn

wrappedCache = {}

def _cmdsGetAttribute_(module, name):
	"""method to supplant normal __getattribute__
	on the cmds module
	use to wrap cmds functions lazily as needed
	functions cached in dict for now,
	not explicitly set back on module yet"""

	#print("_cmdsGetAttribute", module, name)

	# check cache for wrapped function
	if name in wrappedCache:
		return wrappedCache[name]

	# no wrapped exists - retrieve it, wrap it, cache it
	found = object.__getattribute__(module, name)
	# if not isinstance(found, function):
	#if not isinstance(found, builtins.function):
	if not callable(found):
		return found

	patchFn = wrapCmdFn(found)
	wrappedCache[name] = patchFn
	return patchFn



def patchCmdsGetAttr():
	""" patch __getattribute__ on cmds module
	to function above """
	#cmds.__getattribute__ = _cmdsGetAttribute_
	# is this it?
	setattr(cmds, "__getattribute__", _cmdsGetAttribute_)
	print("patched cmds getAttribute")


# this is a way simpler idea
class ModuleDescriptor(object):
	"""wrapper class for a module to implement
	accessors easily"""
	def __init__(self, module):
		self.mod = module

	def __getattribute__(self, item):
		mod = object.__getattribute__(self, "mod")
		return getattr(mod, item)

class CmdsDescriptor(ModuleDescriptor):

	def __getattribute__(self, item):
		if item == "mod" :
			return object.__getattribute__(self, "mod")
		return _cmdsGetAttribute_(self.mod, item)


