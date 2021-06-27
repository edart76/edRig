"""Been having trouble keeping the dependencies correct in this package-
This module is for the simple bases of any higher types we implement
within the maya environment, mainly for use in instance checking
DO NOT IMPORT MAYA CMDS HERE
openmaya is probably fine though

consider this forward-declaration
with python characteristics
"""


from __future__ import annotations
from typing import List, Set, Dict, Callable, Tuple, Sequence, Union, TYPE_CHECKING
from functools import partial


class NodeBase(object):
	pass


class PlugBase(object):
	pass
