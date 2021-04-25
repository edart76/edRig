# fucnctions for renumbering mesh points, getting weights,
# interfacing between weights and maps etc
# additionally for working with nurbs shapes

import math
from six import iteritems, string_types


from edRig import core, attr, transform, naming, cmds, om, oma, con
from edRig.lib.python import AbstractTree
from edRig.node import AbsoluteNode, ECA

def getMObject(node):
	sel = om.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)


def closestPointOnMesh(meshPlug, pos=(0, 0, 0), static=False):
	""" pos may be tuple, plug or mvector """

def getMeshUVs(meshFn):
	""" full map of mesh uv sets by name """
	data = {name : {
		"coords" : meshFn.getUVs(name), # array of u, array of v
		"assigned" : meshFn.getAssignedUVs(name),
		# number of assigned uvs per face, uv ids per face
	} for name in meshFn.getUVSetNames()}

def setMeshUVSet(meshFn, data, name="map1"):
	""" sets individual mesh uv set from data """
	uvData = data[name]
	meshFn.setUVs( uvData["coords"][0], uvData["coords"][1], name)
	meshFn.assignUVs( uvData["assigned"][0], uvData["assigned"][1], name)



def getLiveShapeLayer(target, local=True):
	"""creates new shape node with direct mesh connection to master"""
	newName = naming.incrementName(target)
	newShape = ECA("mesh", newName)
	# cmds.parent(newShape, s=True)
	meshAttr = "outMesh" if local else "worldMesh[0]"
	cmds.connectAttr(target+"."+meshAttr, newShape+".inMesh")
	return newShape


def getMeshInfo(target):
	"""saves mesh vertex positions and connections to data"""
	fn = AbsoluteNode(target).shapeFn

	connectList = []
	countList = []
	for i in range(fn.numPolygons):
		connects = fn.getPolygonVertices(i) # int array
		countList.append(len(connects))
		connectList += [n for n in connects]

	meshInfo = {
		"vertices": [(i.x, i.y, i.z) for i in fn.getPoints()],
		"polygonCounts" : countList,
		"polygonConnects" : connectList,
	}
	# tackle UVs when we need to
	return meshInfo


def setMeshInfo(target, parent, info):
	"""regenerate a mesh from stored info"""

	"""create params:
	vertices - list of MPoints of vertex positions
	polygonCounts - sequence of ints - one per polygon, showing number of verts
	polygonConnects - Indices into the sequence of vertices, 
		mapping them onto the individual polygons. 
		This sequence is partitioned according to the polygonCounts. 
		So if the counts were [3, 4] then the first 3 elements 
		of polygonConnects would be the indices for the first polygon's 
		vertices and the next 4 elements would be the indices for the 
		second polygon's vertices.
	uValues - sequence of floats of indices
	vValues - same
	parent - MObject
	"""
	parent = AbsoluteNode(parent).MObject
	meshObj = om.MFnMesh().create(
		vertices=info["vertices"],
		polygonCounts=info["polygonCounts"],
		polygonConnects=info["polygonConnects"]
	)
	target.setMObject(meshObj)
	return meshObj



def getWeights(targetMesh, targetDeformer, attr):
	"""gets normal weights"""

def getSkinWeights(shape, skin, influenceList=None, weightAttr="weightList"):
	"""returns large tuple of form
	( (weights list for influence i), (for i+1)) etc"""
	skin = AbsoluteNode(skin)
	plug = skin.getMPlug("weightList")



def getPaintable(shape):
	pass

def splitHistoryAtPlug(inputPlug, name="split"):
	"""inserts tweak node directly BEFORE specified plug, allowing
	GPU-safe extraction of mesh data at any point
	:returns plug"""
	driver = attr.getDrivingPlug(inputPlug)
	tweak = ECA("tweak", name=name)
	cmds.connectAttr(driver, tweak+".input[0].inputGeometry")
	return tweak + ".outputGeometry[0]"

def getLiveMatrixOnMesh(meshShape, closeTo):
	"""attach a nurbs surface to nearest face, then get matrix from that"""
	mesh = AbsoluteNode(meshShape).shape
	closePoint = transform.pointFrom(closeTo)
	point, face = getClosestPoint(meshShape, closePoint)
	iterator = om.MItMeshPolygon(mesh.MObject) # use flat init and reset(object) if this fails
	iterator.setIndex(face)
	indices = iterator.getConnectedVertices()
	surface = attachNurbsSurfaceToMesh(mesh, indices)

	# continue with surface uv lookup
	surfPoint, u, v = surface.shapeFn.closestPoint(closePoint) # don't care about point yet
	psi = ECA("pointOnSurfaceInfo", )

def getClosestPoint(meshShape, closeTo):
	"""return index of closest face
	:returns (MPoint closest point, int faceIndex)"""
	point = transform.pointFrom(closeTo)
	mesh = AbsoluteNode(meshShape)
	return mesh.shapeFn.getClosestPoint(point, om.MSpace.kWorld)

def attachNurbsSurfaceToMesh(meshShape, pntList):
	"""attach nurbs surface to target points"""
	nurbs = ECA("nurbsSurface")
	# no checking for crossed surface here
	for i, val in enumerate(pntList):
		cmds.connectAttr(meshShape+".points[{}]".format(val),
		                 nurbs+".controlPoints[{}]".format(i))
	return nurbs

def combineInstanceMeshes(parentTransforms, name="combined"):
	"""combines instanced meshes for deformation as one
	actually a use for the array world mesh attribute \o/ """
	shapes = set(cmds.listRelatives(parentTransforms, shapes=True))
	if len(shapes) > 1:
		print("multiple shapes detected, using first")
	shape = shapes.pop()
	# connect attributes
	combine = name + "_unite"
	mesh = name + "_combined"
	if not cmds.ls(combine):
		combine = ECA("polyUnite", n=combine)
		mesh = ECA("mesh", n=mesh+"Shape")
		mesh.parent.rename(mesh)
	for i in range(len(parentTransforms)):
		con(shape + ".worldMatrix[{}]".format(i),
		    combine + ".inputMat[{}]".format(i))
		con(shape + ".worldMesh[{}]".format(i),
		    combine + ".inputPoly[{}]".format(i))
	con(combine + ".output", mesh + ".inMesh")
	return combine, mesh







"""
weightlist attribute common to deformers
weightList - array, one per mesh
	weightList[0]
		weights - array, one per vertex
			weights[12] - most of the time, just a straight float value
			weights[13]
			weights[14]
this is common across most deformers, and worth assuming for default behaviour


SKINCLUSTERS ARE DIFFERENT
weightList - array, ONE PER VERTEX
	weightList[1]
		weights - array, ONE PER INFLUENCE ON SKINCLUSTER, indexed in sync
			weights[0]
			weights[1] - this would be for three joints
			weights[2]
	weightList[2]
		weights
			weights[0]
			weights[1]
			weights[2]

weights often stored only if they deviate from a base value - a bend deformer is 1
if no weights are painted, arrays remain at [0]


best to do this with a default-override system

override deformer type
	so specify entirely bespoke ways of handling, ie skin
	
override attribute maps
	pick out weights to register
	save weights by default, don't error if something isn't there
	
goal is to have dict of { vertexIndex : weight }
for skins just use list or dict of influences, but store
weights of each influence in the same way

this isn't tom and jerry, so we assume we will have fewer joints in the skin
than vertices in the mesh

"""


def checkItemsUnique(seq):
	""" seq contains no repetitions """
	return len(set(seq)) == len(seq)

def getNameIndexMap(skinNode):
	""" return a map of object : influence index """
	fn = oma.MFnSkinCluster(getMObject(skinNode))
	influences = fn.influenceObjects()
	result = {}

	# check influence names are unique
	infNames = [i.fullPathName().split("|")[-1] for i in influences]
	if not checkItemsUnique(infNames):
		raise RuntimeError("joint names must be unique")

	for inf in influences:
		result[inf.fullPathName().split("|")[-1]] = int(fn.indexForInfluenceObject(inf))
	return result


def getSkinWeights(skinNode):
	"""returns dict of all vertex weighs per influence
	"""
	fn = om.MFnDependencyNode(core.MObjectFrom(skinNode))

	listPlug = fn.findPlug("weightList", False)
	weightPlug = fn.findPlug("weights", False)
	nVertices = listPlug.numElements()
	result = {}

	for vtx in range(nVertices):
		weightPlug.selectAncestorLogicalIndex(vtx, listPlug.attribute())
		# interleaved list of [ indexA, valueA, indexB, valueB] etc
		data = [None] * weightPlug.numElements() * 2
		for idx in range(weightPlug.numElements()):
			valuePlug = weightPlug.elementByPhysicalIndex(idx)
			data[ idx * 2 ] = valuePlug.logicalIndex()
			data[ idx * 2 + 1 ] = valuePlug.asDouble()
		result[vtx] = tuple(data)
	return result


def getSkinData(skinNode):
	return {
		"names" : getNameIndexMap(skinNode),
		"weights" : getSkinWeights(skinNode),
		"formatVersion" : 1 # how do we work with this
	}

def setSkinData(skinNode, skinData):
	""" reapply and reconnect skincluster data """
	# check that all influences are found in scene
	# if not, create temp joints at origin
	influences = getNameIndexMap(skinNode)
	for name, index in skinData["names"].iteritems():
		if not cmds.objExists(name):
			jnt = cmds.createNode("joint", n=name)
			cmds.skinCluster(skinNode, e=1, add=jnt)

	# set skin plug values
	fn = om.MFnDependencyNode(core.MObjectFrom(skinNode))
	listPlug = fn.findPlug("weightList", False)
	weightPlug = fn.findPlug("weights", False)
	nVertices = listPlug.numElements()

	weights = skinData["weights"]

	for vtx, weightData in weights.iteritems():
		weightPlug.selectAncestorLogicalIndex(
			vtx, listPlug.attribute())

		# clear current values
		#for i in range(int(weightPlug.getExistingArrayAttributeIndices())):
		for i in range(int(weightPlug.numElements())):
			valuePlug = weightPlug.elementByPhysicalIndex(i)
			valuePlug.setDouble(0.0)

		for i in range(int(len(weightData) / 2)):
			valuePlug = weightPlug.elementByLogicalIndex(
				weightData[ i * 2]
			)
			valuePlug.setDouble(
				weightData[ i * 2 + 1]
			)


import math


class OffsetBuffer(object):
	""" should be 1:1 of the c++ object
	should also be able to be converted to numpy
	once I understand numpy

	no interleaving for now

	[(3, 2), (4, 5, 6), (5, 6, 5)] 8
	[0,       2,         5 ]
	[ 2 - 0     5 - 2    8 - 5 ]

	could literally just use lists of tuples in python
	"""

	def __init__(self, values, offsets):
		self.values = values
		self.offsets = offsets

	def mapIndex(self, index):
		""" account for negative indexing """
		return index if index >= 0 else len(self.values) + index

	def entryLength(self, index):
		""" length of entry in buffer """
		index = self.mapIndex(index)
		if index == len(self.values) - 1:
			return len(self.values) - self.offsets[-1]
		return self.offsets[index + 1] - self.offsets[index]

	def entry(self, index):
		""" start at the offset to this index,
		continue for the length of this entry """
		index = self.mapIndex(index)
		return self.values[
		       self.offsets[index] :
		            self.offsets[index] + self.entryLength(index) ]

	def __getitem__(self, item):
		index = self.mapIndex(item)
		return self.entry(index)


class Vertex(object):
	""" testing if it's better to have a struct
	for traversing meshes, otherwise it gets super tangled
	also locality probably isn't too bad, since if you want
	to map point to vertex, you usually also need to map
	vertex to point as well """
	def __init__(self, localIndex, face=None):
		self._localIndex = localIndex # FACE-LOCAL vertex index
		#self.next = next # VERTEX object to next vtx
		self.face = face

	@property
	def index(self):
		""" return GLOBAL vertex index """
		return self.localIndex + self.face.vertexOffset

	# interfaces like a proper programmer
	@property
	def globalIndex(self):
		return 0
	@property
	def localIndex(self):
		return self._localIndex
	@property
	def nextVertex(self):
		return 0
	@property
	def prevVertex(self):
		return 0
	# in c these will all be direct functions


class Face(object):
	def __init__(self, index, vertexOffset=None):
		self.index = index
		# value to add to LOCAL vertex indices to retrieve GLOBAL indices
		self.vertexOffset = vertexOffset

	def points(self):
		""" can still index back into main array """
		return faceConnects[self.index]

""" 
for compromise between efficiency and user-friendliness,
consider only generating these components on demand, from the topo buffers
same thing with component attributes
"""

def tupleListFromBuffers(strides, values):
	result = [None] * len(strides)
	for i, stride in enumerate(strides):
		result[i] = tuple(values[:stride])
		values = values[stride:]
	return result

class MeshStruct(object):
	"""
	common interchange serialisation structure to
	store per point attributes
	should be interchangeable with c++ struct output

	TERMINOLOGY:
	POINT : single point coordinate in space, connected by
		edges to other points. The same point may be shared by
		many faces. In MAYA, this would be a 'vertex'.
	FACE : single polygon, spanning many points and containing corresponding
		vertices. In HOUDINI, this would be a 'primitive'.
	VERTEX : single corner of a face, where the face meets a point, but
		UNIQUE to that face. A vertex has a global index, unique in the mesh,
		and a local index, unique within its face.
		In MAYA, this would be a 'face vertex'.

	A cube, with square faces, has:
		- 8 points
		- 6 faces
		- 6 * 4 = 24 vertices

	Maya doesn't seem to consider face vertices as real objects, they
	are literally defined by a face and a (point) vertex. So that's annoying

	We adopt full houdini-style attributes - except for UVs.
	A UV set is literally a separate mesh in its own right, just
	with the same face and vertex indices.

	"""

	def __init__(self,
	             facePointConnects,
	             pointConnects=None,
	             faceVertexConnects=None,
	             pointVertexConnects=None,
	             hasSubMeshes=True, # whatever
	             ):
		""" passing either facePointConnects or faceVertexConnects
		will share these existing buffers instead of recomputing.
		If both are given, we assume that they match, and
		are topologically correct.
		"""
		flatPoints = flatten(facePointConnects)
		self.nPoints = max(flatPoints) + 1
		self.nFaces = len(facePointConnects)
		self.nVertices = len(flatPoints)

		# topo buffers
		self.facePointConnects = facePointConnects # most important
		if pointConnects:
			self.pointConnects = pointConnects
		else:
			self.pointConnects = self.pointConnectsFromFacePointConnects(
				self.facePointConnects )

		if faceVertexConnects:
			self.faceVertexConnects = faceVertexConnects
		else:
			self.faceVertexConnects = self.faceVertexConnectsFromFacePointConnects(
				self.facePointConnects,)

		if pointVertexConnects:
			self.pointVertexConnects = pointVertexConnects
		else:
			self.pointVertexConnects = self.buildPointVertexConnects(
				self.nPoints,
				self.facePointConnects,
				self.faceVertexConnects
			)

		# lazy compute buffers
		self.vertexToFacePointMap = None

		# per-element attributes
		self.meshAttrs = {}
		self.faceAttrs = {}
		self.pointAttrs = {}
		self.vertexAttrs = {}
		# can easily be used with int values to track groups

		if hasSubMeshes:
			# special cases
			self.subMeshes = {
				"UVs" : {},
			}
			# we store uv-varying attributes in the uv mesh structs
		else: self.subMeshes = None

	def faceVertexBuffers(self, local=False):
		faces, allVertices = [], []
		for face, vertices in enumerate(self.faceVertexConnects):
			for localVtx, globalVtx in enumerate(vertices):
				faces.append(face)
				allVertices.append(localVtx if local else globalVtx)
		return faces, allVertices

	def facePointBuffers(self, local=False):
		faces, allVertices = [], []
		for face, vertices in enumerate(self.faceVertexConnects):
			for localVtx, globalVtx in enumerate(vertices):
				faces.append(face)
				allVertices.append(localVtx if local else globalVtx)
		return faces, allVertices

	def facePointsFromVertices(self):
		""" list [ vertex index : (face index, point index) ] """
		if not self.vertexToFacePointMap :
			result = [None] * self.nVertices
			vtxIndex = 0
			for face, points in enumerate(self.facePointConnects):
				for point in points:
					result[vtxIndex] = (face, point)
					vtxIndex += 1
			self.vertexToFacePointMap = result
		return self.vertexToFacePointMap


	def iterFaceVertices(self, local=False):
		""" return tuples of (face, globalVtx) """
		return zip(self.faceVertexBuffers(local))

	@classmethod
	def fromMFnMesh(cls, mfn):
		""" generate a MeshStruct from a maya mfn mesh
		:param mfn : om.MFnMesh """

		faceCounts, facePoints = mfn.getVertices()
		facePointConnects = tupleListFromBuffers(
			faceCounts, facePoints)

		mesh = cls(facePointConnects,
		           )

		# set attributes
		# positions
		positions = [tuple(i)[:3] for i in mfn.getPoints()]
		mesh.pointAttrs["positions"] = positions

		# normals
		baseNormals = mfn.getNormals()
		normalCounts, normalIds = mfn.getNormalIds()
		# this was quite silly to arrive at, but it works
		normals = []
		for i in range(mesh.nVertices):
			normal = baseNormals[ normalIds[ i ] ]
			normals.append(normal)
		normals = [tuple(i) for i in normals]
		mesh.vertexAttrs["normals"] = normals

		# UVs
		uvSets = {}

		# for setName in fn.getUVSetsInFamily(familyName):
		for setName in mfn.getUVSetNames() or []:

			#create UV sub-mesh
			uvPositions = [tuple(i) for i in mfn.getUVs(setName)]

			faceUVIds = [
				[mfn.getPolygonUVid(face, n, setName) for n in
				 range(len(mfn.getPolygonVertices(face)))]
				for face in range(mfn.numPolygons)]

			uvConnects = cls.pointConnectsFromFacePointConnects(
				faceUVIds)

			uvMesh = MeshStruct(
				facePointConnects=faceUVIds,
				pointConnects=uvConnects,

				# share vertex information from base mesh
				faceVertexConnects=mesh.faceVertexConnects,
				#pointVertexConnects=mesh.pointVertexConnects,
				hasSubMeshes=False
			)
			uvMesh.pointAttrs["positions"] = uvPositions

			uvSets[setName] = uvMesh
		mesh.subMeshes["UVs"] = uvSets

		return mesh

	def toMFnMesh(self, mfn=None):
		""" convert a MeshStruct to a maya mesh object
		:param mfn : om.MFnMesh """
		mfn = mfn or om.MFnMesh()
		positions = self.pointAttrs["positions"]
		positions = [om.MPoint(*i) for i in positions]
		faceCounts = [len(i) for i in self.facePointConnects]
		faceConnects = flatten(self.facePointConnects)

		mfn.create(positions, faceCounts, faceConnects) # works

		# assign attributes
		# normals

		# maya requires pairs of (face index, point index) to define vertices
		faces = [i[0] for i in self.facePointsFromVertices()]
		points = [i[1] for i in self.facePointsFromVertices()]

		mfn.unlockFaceVertexNormals(faces, points)
		if self.vertexAttrs.get("normals"):
			for n in range(len(faces)):
				mfn.setFaceVertexNormals(
					# [om.MVector(*i) for i in self.vertexAttrs["normals"]][:5],
					[om.MVector(*self.vertexAttrs["normals"][n])],
					[faces[n]], [points[n]]
				)

		# UVs
		for setName, uvMesh in iteritems(self.subMeshes["UVs"]):
			self.applyUVsMFnMesh(mfn, setName, uvMesh)


	@staticmethod
	def applyUVsMFnMesh(mfn, uvSetName, uvMesh, setCurrent=True):
		""" applies a specific UV mesh as a maya uv set
		optionally sets it to be the current active set """
		if not uvSetName in mfn.getUVSetNames():
			mfn.createUVSet(uvSetName)
		mfn.clearUVs(uvSetName)
		mfn.setUVs(uvMesh.pointAttrs["positions"][0],
		           uvMesh.pointAttrs["positions"][1],
		           uvSet=uvSetName)
		mfn.assignUVs(
			[len(i) for i in uvMesh.facePointConnects],
			flatten(uvMesh.facePointConnects),
			uvSetName
		)
		if setCurrent:
			mfn.setCurrentUVSetName(uvSetName)


	def serialise(self):
		""" flatten mesh data to dict """
		data = {k : getattr(self, k) for k in [
			"facePointConnects",	"pointConnects",
		    "faceVertexConnects", "pointVertexConnects",
			"pointAttrs", "faceAttrs", "vertexAttrs", "meshAttrs"
		]}
		# submeshes
		if self.subMeshes:
			subData = {"UVs" : {}}
			for name, subMesh in iteritems(self.subMeshes["UVs"]):
				subData["UVs"][name] = subMesh.serialise()
			data["subMeshes"] = subData
		return data

	@classmethod
	def fromDict(cls, data):
		""" restore full mesh object from dictionary """
		# regenerate main mesh object
		initKwargs = {k : data.get(k) for k in [			"facePointConnects",	"pointConnects",
		    "faceVertexConnects", "pointVertexConnects"] }
		hasSubMeshes = "subMeshes" in data
		initKwargs["hasSubMeshes"] = hasSubMeshes
		mesh = cls(**initKwargs)
		# set attributes
		for k in ["pointAttrs", "faceAttrs",
		          "vertexAttrs", "meshAttrs"]:
			setattr(mesh, k, data.get(k) or {} )
		# regenerate and set submeshes
		if hasSubMeshes:
			subData = {
				"UVs" : {
					name : cls.fromDict(subData) for name, subData in
						iteritems(data["subMeshes"]["UVs"])
				}
			}
			mesh.subMeshes = subData
		return mesh



	@staticmethod
	def groupConnectedElements(connects):
		""" given ordered list of connect tuples,
		walk through the set and group all connected elements
		into indexed sets
		this assumes bidirectional connections in the elements """
		groups = []
		visited = [0] * len(connects)
		groupIdx = 0
		visitIdx = 0
		while 1 - any(visited):
			pass


	@staticmethod
	def facePointConnectsFromPointConnects(pointConnects):
		""" given list of [point index : (connected points)]
		returns new list of tuples -
		[ face index : (face points) ]

		so I think this is actually intractable, it becomes a question
		of picking shortest closed paths, but there is no information
		on whether those paths are valid
		"""
		faceSets = {}
		# many-to-few dict of {point index : whole face set}
		faceIdx = 0
		faceIdxRef = [0]

		print(pointConnects)
		for i, points in enumerate(pointConnects):
			span = len(points)
			for n, pt in enumerate(points):
				lead = (n + 1 + span) % span
				lead = points[lead]
				trail = (n - 1 + span) % span
				trail = points[trail]

				# new pair of points means new face
				if not (lead in faceSets and trail in faceSets):
					faceSet = {lead, trail}
					faceSets[lead] = faceSet
					faceSets[trail] = faceSet


				for adjPt in [lead, trail]:
					if not adjPt:
						pass
				faceSets[n].add(n)
		#return list(faceSets.values())
		return faceSets

	@staticmethod
	def faceVertexConnectsFromFacePointConnects(facePointConnects):
		""" given list of [face index : (face points)
		return new list of tuples -
		[face index : (face global vertices) ]

		consider also returning point map from this """
		nFaces = len(facePointConnects)
		faceVertexConnects = [None] * nFaces
		vtxIdx = 0

		for face in range(nFaces):
			# # global point connections
			facePoints = facePointConnects[face]
			faceVertices = [-1] * len(facePoints)
			for n, point in enumerate(facePoints):
				faceVertices[n] = vtxIdx
				vtxIdx += 1
			faceVertexConnects[face] = tuple(faceVertices)
		return faceVertexConnects

	@staticmethod
	def buildPointVertexConnects(nPoints, facePointConnects, faceVertexConnects):
		""" given list of [face index : (face points) ],
		and [face index : (face vertices) ],
		return list of [ point index : (point vertices) ]
		"""
		### FASCINATING behaviour I found ###
		# pointVertexConnects = [[]] * nPoints
		# this does not create a list of many lists
		# it creates a list with many entries - of THE SAME LIST

		pointVertexConnects = []
		for i in range(nPoints):
			pointVertexConnects.append([])

		for points, vertices in zip(
				facePointConnects, faceVertexConnects):
			for point, vertex in zip( points, vertices):
				pointVertexConnects[point].append(vertex)
		return pointVertexConnects



	@staticmethod
	def pointConnectsFromFacePointConnects(facePointConnects):
		""" very long function names
		because this buffer stuff is so easy to lose track of
		given list of [face index : (face points)]
		return new list of tuples -
		[point index : (connected points)]
		"""
		pointSets = {}
		for i, points in enumerate(facePointConnects):
			span = len(points)
			for n, pt in enumerate(points):
				lead = (n + 1 + span) % span
				trail = (n - 1 + span) % span
				# point connects are inherently orderless
				# order only appears if you consider faces between them
				if not pt in pointSets:
					pointSets[pt] = set()
				pointSets[pt].add(points[lead])
				pointSets[pt].add(points[trail])
		return [tuple(i) for i in pointSets.values()]

def flatten(seq):
	""" recursively flatten sequence to list """
	result = []
	for i in seq:
		if hasattr(i, "__iter__"):
			result.extend(flatten(i))
		else:
			result.append(i)
	return result

"""

from edRig import mesh, om, cmds
reload(mesh)


mObj = mesh.getMObject("meshShape")
mfn = om.MFnMesh(mObj)

meshObj = mesh.MeshStruct.fromMFnMesh(mfn)

meshObj.toMFnMesh()

"""

class SkinWeights(object):

	pass


class DeformerWeights(object):
	""" per-point varying weights """



class DeformerWrapper(object):
	"""interface for setting and getting weights"""

	def __init__(self, deformerNode):
		self.defaults = {
			"default": {
				"weightList": self.getGenericWeights},
			"skinCluster": {
				"weightList": self.getSkinWeights,
				"blendWeights": self.getGenericWeights}
		} # tried to make this a class attribute, but couldn't
		# work out how to direct to call instance methods

		self.node = AbsoluteNode(deformerNode)
		self.deformerType = self.node.MFnDependency.typeName
		print( "new deformer wrapper is type {}".format(self.deformerType))

		if self.node.MObject.hasFn(681): # skinClusterFilter
			self.fn = oma.MFnSkincluster(self.node.MObject)
		else:
			self.fn = oma.MFnGeometryFilter(self.node.MObject)

		if self.deformerType in self.defaults.keys():
			self.treatment = self.defaults[self.deformerType]
		else:
			self.treatment = self.defaults["default"]
		self.attrs = self.treatment.keys()

	def getComponentObject(self):
		setFn = om.MFnSet(self.fn.deformerSet())
		members = setFn.getMembers(True) # MSelectionList, flatten=True
		print( "members is {}".format(members) )






	def getSkinWeights(self):
		"""returns dict of all vertex weighs per influence
		copied in part from charactersetup.com"""
		returnDict = {}
		influences = self.fn.influenceObjects() # MDagPathArray
		numInfluences = len(influences)

		wlPlug = self.fn.findPlug("weightList")
		wlAttr = wlPlug.attribute()
		wPlug = self.fn.findPlug("weights")
		wAttr = wPlug.attribute()


		# create a dict whose key is MPlug index and value is influenceList index
		infIds = {}
		for i in range(numInfluences):
			#returnDict[i] = {}
			infId = int(self.fn.indexForInfluenceObject(influences[i]))
			#infIds[infId] = i
			returnDict[infId] = {}

			for n in xrange(wlPlug.numElements()):
				# iterating over all vertices

				# point the wPlug to index representing this vertex
				wPlug.selectAncestorLogicalIndex(n, wlAttr)

				# we keep zero-weights for now, unless they get slow
				# copying an MPlug every vertex also seems slow
				vPlug = om.MPlug(wPlug)
				vPlug.selectAncestorLogicalIndex(i, wAttr)
				try:
					returnDict[infId][n] = vPlug.asDouble()
				except KeyError:
					pass

		return returnDict

	def setSkinWeights(self, weightsDict):
		pass






	def getGenericWeights(self, weightAttr):
		"""used for any attribute of the normal weightsList form"""



	def setMapAttrs(self, attrs=None):
		"""override maps to save on a specific wrapper"""
		self.attrs = attrs

	def gatherAllWeights(self):
		"""return dict in format of:
		{ "blendWeights" : { # attrName
			0 : 0.2, # dict as returned by specific function
			2 : 0.4},
		"weightList : {
			[
				{ 0 : 0.2,
				4 : 0.5,
				5 : 0.7 },
				{ 3 : 0.1,
				 2 : 0.1 }
			]
		} etc"""
		pass


"""

cmds.addAttr( ln="testArray", dt="doubleArray")
cmds.makePaintable("pSphere1.testArray", attrType="doubleArray")


"""



