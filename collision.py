from edRig import con
from edRig.maya.core.node import AbsoluteNode, ECA


def collidePoint(collisionTransform, collisionMesh=None,
                 preserveLength=True):
	"""help
	only mesh colliders for now"""
	collider = AbsoluteNode(collisionMesh).shape
	tf = AbsoluteNode(collisionTransform)
	cpa = ECA("closestPointOnMesh", n="closestPointOnMesh")
	cpw = ClosestPoint(cpa, kind="mesh")
	cpa.con(collider.outWorld, cpw.inShape)

	# no support for ease-in yet, but there could be

	condition = ECA("condition", n="surfaceCondition")
	depth = ECA("distanceBetween", n="collisionDepth")
	mainVec = ECA("plusMinusAverage", n="vecToPoint")

	dot = ECA("vectorProduct", n="dotProduct")

	dot.set("normalizeOutput", 1)
	dot.set("operation", 1) # dot product, redundant but just in case

	mainVec.set("operation", 2) # subtract

	con(tf+".translate", mainVec+".input3D[0]")
	con(cpw.outPos, tf+".input3D[1]")

	con(mainVec+".output3D", depth+".point1")

	condition.set("operation", 2) # greater than
	# is dot product greater than 0
	con(dot+".outputX", condition+".firstTerm")
	con(cpw.outPos, condition+".colorIfFalse")
	con(tf+".translate", condition+".colorIfTrue")





class ClosestPoint(object):
	"""wrapper around a wrapper around a node"""
	collisionInfo ={
		"nurbsSurface" : {

		},
		"mesh" : {
			"shape" : {
				"inShape" : "inMesh",
				"outLocal" : "outMesh",
				"outWorld" : "worldMesh[0]"
			},
			"cpn" : {
				"inShape" : "inMesh",
				"inPos" : "inPosition",
				"outPos" : "position",
				"outUV" : ("parameterU", "parameterV"),
				"outNormal" : "normal"
			}
		}
	}
	def __init__(self, node, kind="mesh"):
		self.node = node
		self.kind = kind
		self.cpInfo = self.collisionInfo[kind]["cpn"]
		self.shapeInfo = self.collisionInfo[kind]["shape"]

	@property
	def inPos(self):
		return self.node+"."+self.cpInfo["inPos"]
	@property
	def inShape(self):
		return self.node+"."+self.cpInfo["inShape"]
	@property
	def outPos(self):
		return self.node+"."+self.cpInfo["outPos"]
	@property
	def outNormal(self):
		return self.node+"."+self.cpInfo["outNormal"]