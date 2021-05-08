

from six import iteritems
import json
import sys, os
from maya import cmds, mel
from maya.api import OpenMaya as om, OpenMayaAnim as oma

import math

def getMObject(node):
	sel = om.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)

# deformer weight extractions
# by default return array of [point index : juicy goss]

def extractDeltaMushWeights(node, weightAttr):
	"""given a basic float array plug, return array of floats
	only considers deformers on a single piece of geometry"""
	mfnDep = om.MFnDependencyNode(getMObject(node))
	plug = mfnDep.findPlug(weightAttr, 0)
	weightListAttr = mfnDep.attribute("envelopeWeightsList")
	plug.selectAncestorLogicalIndex(0, weightListAttr)

	# 0 if weights have not been painted
	nElements = plug.numElements()
	if not nElements:
		return None

	data = [None] * nElements

	for i in range(nElements):
		child = plug.elementByPhysicalIndex(i)
		data[i] = child.asDouble()
	return data

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
	fn = om.MFnDependencyNode(getMObject(skinNode))

	listPlug = fn.findPlug("weightList", False)
	weightPlug = fn.findPlug("weights", False)
	nVertices = listPlug.numElements()
	result = [None] * nVertices

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
	for name, index in list(skinData["names"].items()):
		if not cmds.objExists(name):
			jnt = cmds.createNode("joint", n=name)
			cmds.skinCluster(skinNode, e=1, add=jnt)

	# set skin plug values
	fn = om.MFnDependencyNode(getMObject(skinNode))
	listPlug = fn.findPlug("weightList", False)
	weightPlug = fn.findPlug("weights", False)
	nVertices = listPlug.numElements()

	weights = skinData["weights"]

	for vtx, weightData in enumerate(weights):
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
		#return faceConnects[self.index]

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



def flatten(seq):
	""" recursively flatten sequence to list """
	result = []
	for i in seq:
		if hasattr(i, "__iter__"):
			result.extend(flatten(i))
		else:
			result.append(i)
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
	             mfn=None, # optional
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

		# optional
		self.mfn = mfn

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
		self.wholeAttrs = {}
		self.faceAttrs = {}
		self.pointAttrs = {"positions" : []}
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
		return list(zip(self.faceVertexBuffers(local)))

	# region dcc specific
	# region maya

	@classmethod
	def fromShape(cls, shapeNode):
		mobj = getMObject(shapeNode)
		return cls.fromMFnMesh(om.MFnMesh(mobj))

	@classmethod
	def fromMFnMesh(cls, mfn):
		""" generate a MeshStruct from a maya mfn mesh
		:param mfn : om.MFnMesh """

		faceCounts, facePoints = mfn.getVertices()
		facePointConnects = tupleListFromBuffers(
			faceCounts, facePoints)

		mesh = cls(facePointConnects,
		           mfn=mfn)

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

		positions = self.pointAttrs["positions"]
		positions = [om.MPoint(*i) for i in positions]
		faceCounts = [len(i) for i in self.facePointConnects]
		faceConnects = flatten(self.facePointConnects)
		if not mfn:
			mfn = om.MFnMesh()
			mfn.create(positions, faceCounts, faceConnects) # works

		else:
			mfn.setPoints(positions)
		# assign attributes
		# normals

		# maya requires pairs of (face index, point index) to define vertices
		faces = [i[0] for i in self.facePointsFromVertices()]
		points = [i[1] for i in self.facePointsFromVertices()]

		#mfn.unlockFaceVertexNormals(faces, points)
		# no difference
		# normals disabled for now, it is SOOO SLOOOOOOOOW
		# if self.vertexAttrs.get("normals"):
		# 	for n in range(len(faces)):
		# 		mfn.setFaceVertexNormals(
		# 			# [om.MVector(*i) for i in self.vertexAttrs["normals"]][:5],
		# 			[om.MVector(*self.vertexAttrs["normals"][n])],
		# 			[faces[n]], [points[n]]
		# 		)

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

	# endregion
	# endregion

	# region IO methods

	def serialise(self):
		""" flatten mesh data to dict """
		data = {k : getattr(self, k) for k in [
			"facePointConnects",	"pointConnects",
		    "faceVertexConnects", "pointVertexConnects",
			"pointAttrs", "faceAttrs", "vertexAttrs", "wholeAttrs"
		]}
		# submeshes
		if self.subMeshes:
			subData = {"UVs" : {}}
			for name, subMesh in iteritems(self.subMeshes["UVs"]):
				subData["UVs"][name] = subMesh.serialise()
			data["subMeshes"] = subData
		else: data["subMeshes"] = {}
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
		          "vertexAttrs", "wholeAttrs"]:
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

	def serialiseToComponents(self):
		""" serialises and returns flattened dict for
		 easier saving to file """
		rich = self.serialise()
		# mesh is only its topology
		flat = {"mesh" : {i : rich[i] for i in
		        ("facePointConnects", "pointConnects",
		         "faceVertexConnects", "pointVertexConnects")}}
		# attributes
		for i in ("point", "face", "vertex", "whole"):
			key = i + "Attrs"
			for k, v in list(rich[key].items()): # individual point attributes
				compName = i + "_" + k
				# positions becomes point_positions
				flat[compName] = v
		# submeshes (uv sets)
		# uvsets are serialised whole, so that they can be applied as one
		# also nobody's trying to apply UV-space positions to anything but uvs
		for k, v in list(rich["subMeshes"].get("UVs", {}).items()):
			compName = "subMesh_" + k
			flat[compName] = v
		print((list(flat.keys())))
		return flat

	@staticmethod
	def saveComponentsToFiles(folder, flatData):
		""""""
		for k, v in list(flatData.items()):
			json.dump(v, open(os.path.join(folder, k) + ".json", "w"))

	# endregion



	# region main abstract topo methods

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
		return [tuple(i) for i in list(pointSets.values())]

	# endregion
