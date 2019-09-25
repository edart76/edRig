""" don't really know what to do with this stuff
basically things to generate things algorithmically from maya """
from __future__ import print_function

from maya import cmds
from edRig import deformer, AbsoluteNode, ECA, dynamics, muscle
from edRig.tools.ui.setup import UiTool
from edRig.lib.python import getUserInput

from edRig.lib import algorithms

def buildGrayCodePattern(n=4, rowWidth=1.0):
	""" generates a full cycle of a Gray code, of 'bit depth' n
	creates a set of square planes """

	code = algorithms.grayCode(n)
	planes = []
	for i, step in enumerate(code):
		# step is "0010" or equivalent
		for n, byte in enumerate(step):
			plane = cmds.polyPlane( subdivisionsX=1, subdivisionsY=1, ch=0 )[0]
			planes.append(plane)
			cmds.setAttr( plane + ".translateX", i )
			cmds.setAttr( plane + ".translateZ", n )
			if int(byte):
				cmds.setAttr( plane + ".translateY", 1)
			cmds.setAttr( plane + ".scaleZ", rowWidth)
	codeTiles = cmds.polyUnite(planes, ch=0)
	return codeTiles









