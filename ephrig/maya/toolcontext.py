
from types import FunctionType
import weakref

from maya import cmds
from maya.api import OpenMaya as om, OpenMayaAnim as oma

import networkx as nx
from tree import Tree

from edRig.ephrig.node import EphNode

nodeObjMap = weakref.WeakValueDictionary()

def getMObject(node):
	uid = cmds.ls(node, uuid=1)
	if nodeObjMap.get(uid):
		return nodeObjMap[uid]
	sel = om.MSelectionList()
	sel.add(node)
	obj = sel.getDependNode(0)
	nodeObjMap[uid] = obj
	return obj


class MayaToolContext(object):
	""" Object for tracking nurbs curve / screenspace
	stroke context

	by default right mouse does not create press events
	"""

	def __init__(self, name):
		self.name = name

	# live context properties
	@property
	def anchorPos(self):
		"""mouse screen original press coords"""
		return cmds.draggerContext(self.name, q=1, anchorPoint=1)
	@property
	def dragPos(self):
		"""mouse screen end drag coords"""
		return cmds.draggerContext(self.name, q=1, dragPoint=1)
	@property
	def button(self):
		"""mouse buttons pressed
		returns 1 for LMB, 2 for MMB, and 1 for literally anything else
		"""
		return cmds.draggerContext(self.name, q=1, button=1)
	@property
	def modifier(self):
		"""modifier buttons pressed
		:returns 'none', 'shift' or 'ctrl' - 'ctrl' has priority """
		return cmds.draggerContext(self.name, q=1, modifier=1) #type:str

	# context mouse methods
	def initialise(self):
		""" called before drag begins, use to set up context
		called on context enter"""
		#print("initialise")

	def onPrePress(self):
		"""Called on each mouse press"""
		#print("onPrePress")

	def onPress(self):
		"""when mouse is pressed"""

	def onDrag(self):
		""" when mouse is dragged """

	def onRelease(self):
		print("onRelease")
		print("button", self.button)
		print("modifier", self.modifier)
		print("dragPos", self.dragPos)

	def onHold(self): # not called?
		print("onHold")

	def exit(self):
		""" called when context exits"""

	def reset(self):
		""" python-facing, to reset context to a new state"""
		print("reset")

	def register(self):
		""" registers tool context with maya """
		if cmds.contextInfo(self.name, exists=1):
			cmds.deleteUI(self.name, toolContext=1)
			self.reset()

		cmds.draggerContext(self.name,
		                    initialize=self.initialise,
		                    prePressCommand=self.onPrePress,
		                    pressCommand=self.onPress,
		                    dragCommand=self.onDrag,
		                    releaseCommand=self.onRelease,
		                    holdCommand=self.onHold,

		                    finalize=self.exit,

		                    )

	def activate(self):
		cmds.setToolTo(self.name)






