
from __future__ import annotations

from functools import partial, wraps
from tree import Tree, Signal
from tree.ui.lib import KeyState, keyDict
from typing import TYPE_CHECKING, Union, Dict, List
from weakref import WeakSet, WeakValueDictionary, WeakKeyDictionary
# ugly fake imports for type hinting
if TYPE_CHECKING:
	from edRig.tesserae.ui2.abstractview import AbstractView
	from edRig.tesserae import AbstractGraph


# scene holding visual node graph
from PySide2 import QtCore, QtWidgets, QtGui
#from edRig.tesserae.ui2.abstracttile import AbstractTile, Knob, Pipe
from edRig.tesserae.ui3.abstracttile import AbstractTile, Knob, Pipe
#from edRig.tesserae.ui2.abstractview import AbstractView
from edRig.tesserae.abstractgraph import AbstractGraph
from edRig.tesserae.abstractnode import AbstractNode
from edRig.tesserae.abstractedge import AbstractEdge

"""functions for graph layout and relaxing
going for simple spring setup

n-squared 

"""

separation = 10.0

expand = 20
margins = QtCore.QMargins(expand, expand, expand, expand)

def getForce(tile:AbstractTile)->QtGui.QVector2D:
	"""for given tile, return resultant force acting upon it
	check each corner of the node for intersection
	"""

	# rect = QtCore.QRectF(tile.boundingRect())
	rect = QtCore.QRectF(tile.sceneBoundingRect().marginsAdded(margins))
	# rect = QtCore.QRectF(*tile.getSize())
	scene = tile.scene()
	# get intersecting tiles
	items = scene.items(rect)
	# remove this tile and any pipes (for now)
	#items.remove(tile)
	items = tuple(filter(lambda x: isinstance(x, AbstractTile), items))
	sumForce = QtGui.QVector2D(0, 0)

	print(rect)
	for i in items: #type: AbstractTile
		if i is tile:
			continue

		print("item", i.abstract.name)
		#print(i.boundingRect())
		# get intersection
		# iRect = rect.intersected(i.boundingRect())
		iRect = rect.intersected(i.sceneBoundingRect())
		#print("iRect", iRect)
		# get span of intersection
		span = QtGui.QVector2D(iRect.bottomRight() - iRect.topLeft()).length()
		print("span", span)
		fDir = QtGui.QVector2D(rect.center() - iRect.center()).normalized()
		# fDir = QtGui.QVector2D(iRect.center()) -QtGui.QVector2D(rect.center())
		print(iRect.center(), rect.center())
		print(fDir)
		force = fDir * span
		sumForce = sumForce + force
	return sumForce * 0.4















