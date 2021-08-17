
"""
asset wrapper object
"""


from __future__ import annotations
import typing as T
import sys, os, pathlib, json, pprint
from functools import partial
from collections import defaultdict

from edRig.dev.assetlib import constant, index, ref

class Asset(object):

	def __init__(self, uid):
		self.uid = uid
		pass
