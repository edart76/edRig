# layers for control of curves
# so basically for control of everything

import maya.cmds as cmds
import edRig.core as core
# tilepile is here to save our souls
from edRig.core import con, ECN
from edRig.tilepile.ops.layer import LayerOp
import edRig.curve as curve
import edRig.control as control
from nodule import nodule
from edRig import control, transform
import sys
sys.dont_write_bytecode = True


class CurveFromPointsOp(LayerOp):
	"""create curve from arbitrary points
	options for cv or ep behaviour"""



