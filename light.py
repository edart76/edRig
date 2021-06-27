from edRig.maya.core.node import ECA
from edRig.control import FkControl

def makePhysicalSunSky(name="sunSky", control=True):
	"""make arnold physical sun and sky with a control"""

	skyDome = ECA("aiSkyDomeLight", n=name+"_skyDome")
	skyNode = ECA("aiPhysicalSky", n=name+"_skySource")

	skyNode.con(skyNode+".outColor", skyDome+".color")

	skyCtrl = FkControl(name=name)
