
"""lib for core openmaya stuff
mainly MObject cache"""

from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
from functools import partial
from enum import Enum
import pprint

from weakref import WeakValueDictionary, WeakSet
from edRig import cmds, om

#mObjRegister = WeakValueDictionary()
mObjRegister = {} # MObjects can't be weakref'd for some reason

def getMObject(node):
	node = str(node)
	if not cmds.objExists(node):
		return None
	uid = cmds.ls(node, uuid=1)[0]

	if mObjRegister.get(uid):
		obj = mObjRegister[uid]
		if obj.isNull():
			raise RuntimeError("object for ", node, " is invalid")
		return obj
	sel = om.MSelectionList()
	sel.add(node)
	obj = sel.getDependNode(0)
	mObjRegister[uid] = obj
	return obj



