
from __future__ import annotations

""" outer holder class for actual tesserae program """

import pprint
from weakref import WeakSet, WeakValueDictionary
from collections import defaultdict
from typing import List, Callable, Dict, Union, Set, TYPE_CHECKING
from functools import partial
from enum import Enum

import os, sys, json, fnmatch

from importlib import reload
from tree import Tree, Signal

from edRig.tesserae.abstractgraph import AbstractGraph

class TesseraeProgram(object):
	pass