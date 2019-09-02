"""oh hey look it's a legit thing that tech artists do"""
from edRig import pipeline, attr, node, camera, AbsoluteNode, ECA
from maya import cmds

def renderView(path=None, asset=None,
               fileType="exr", renderer="arnold",
               width=1920, height=1080,
               camera=None,):
	"""honestly i don't know what i'm doing here"""

	# get main params from camera

	if renderer == "arnold":
		try:
			"""an entire api module with NO DOCUMENTATION how amazing"""
			from mtoa.cmds.arnoldRender import arnoldRender
		except ImportError:
			raise RuntimeError("unable to import arnold, cannot render")

		attr.setAttr("defaultArnoldDriver.ai_translator", fileType)
		attr.setAttr("defaultArnoldDriver.pre", path)

		arnoldRender(width, height)




def renderDepth(path=None, asset=None,
                fileType="png", width=500, height=500,
                objects=None, camera=None):
	"""create a samplerInfo depth setup for normalised 0-1 height
	thank you lewis pickston """
	sampler = ECA("samplerInfo", n="depthSamplerInfo")
	rmv = ECA("remapValue", n="depthRemap")
	material = None
	# mult = ECA("multiplyDivide")
	#
	# mult.set("input1", -1)
	# sampler.con("pointCamera", mult+".input2")
	sampler.con("pointCameraZ", rmv + ".inputValue")
	rmv.con("outColor", material + ".outColor")



"""

from mtoa.cmds.arnoldRender import arnoldRender
arnoldRender(1920, 1080, True, True,'camera1', ' -layer defaultRenderLayer')

# Rendering :
# from mtoa.cmds.arnoldRender import arnoldRender
arnoldRender(1, 1, True, True,'camera1', ' -layer defaultRenderLayer')

cmds.setAttr("defaultArnoldDriver.ai_translator", "png", type="string")
cmds.setAttr("defaultArnoldDriver.pre", "file_name", type="string")

arnoldRender(200, 200, True, True,'camera1', ' -layer defaultRenderLayer')
Here's what I got.

 

These two commands names and sets the file format of the output image:

cmds.setAttr("defaultArnoldDriver.ai_translator", "png", type="string")
cmds.setAttr("defaultArnoldDriver.pre", "file_name", type="string")
I still don't know what the third and fourth parameters of the arnoldRender() function do.

"""

"""'
ARV options on default arnold render settings node
AOVs=Z;Test Resolution=100%;Camera=topShape;
Debug Shading=Disabled;Color Management.Gamma=1;
Color Management.Exposure=0;Background.BG=BG Color;
Background.Color=0 0 0;Background.Image=;Background.Scale=1  1;
Background.Offset=0  0;Background.Apply Color Management=0;
Foreground.Enable FG=0;Foreground.Image=;Foreground.Scale=1  1;
Foreground.Offset=0  0;Foreground.Apply Color Management=1;

"""
