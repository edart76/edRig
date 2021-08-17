

"""
this is basically a database table of uid : data
could be shifted into an actual database with minimal effort,
just replace the interface functions provided here


string "path" represents fractal tree of assets -
path is changeable.
an asset may be a leaf or trunk, containing other assets

if an asset's path is /root/branch/leaf , where /root/branch does not exist,
for now treat as valid, with /root/branch being considered an empty proxy asset where necessary for display.

actual asset entries have no concept of hierarchy - rely on interface methods to rename all child assets with a parent, so none is left behind

Matt Harrad suggested a system where all assets are stored in totally flat folder hierarchy, named only by uuid - I'm not brave enough for that yet

an asset's path still maps to its placement on disk

"""

from __future__ import annotations
import typing as T
import sys, os, pathlib, json, pprint
from functools import partial
from collections import defaultdict




