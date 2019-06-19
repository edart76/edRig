
from edRig.node import AbsoluteNode, ECA
from edRig import transform

class Camera(AbsoluteNode):
	""""""

class CubeMapCamera(object):
	"""creates six cameras correctly oriented for generating
	environment cubemaps"""

	directionMap = {
		"north" : (0,0,1),
		"east" : (1,0,0),
		"south" : (0,0,-1),
		"west" : (-1,0,0),
		"out" : (0,1,0),
		"in" : (0,-1,0)
	}

	def __init__(self):
		self.cameras = {
			k : Camera.create(name=k)
			for k in self.directionMap.keys()
		}
		self.orientCameras()
		self.unifyCameras()

	def orientCameras(self):
		"""aligns cameras consistently to the correct planes"""
		for k, v in self.cameras:
			vector = self.directionMap[k]
			transform.aimToVector(v.transform, vector)

	def unifyCameras(self):
		"""connects all meaningful camera attributes
		north is master"""



