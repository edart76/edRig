# lib for adding and modifying attributes
import random

from tree import Tree

from edRig.lib import python
from edRig.dcc import cmds, om


dimTypes = {
	"0D" : ("matrix",),
	"1D" : ("nurbsCurve", "bezierCurve"),
	"2D" : ("nurbsSurface", "mesh")
}

nodeObjMap = {}

def treeFromPlug(rootPlug):
	""" retrieve a tree with branches representing nested plugs,
	containing useful information about them
	hopefully we can eventually replace most of the other mess below """
	node, at = rootPlug.split(".")

	tree = Tree(name=at, val=rootPlug)
	for i in cmds.attributeQuery(at, node=node, listChildren=1) or []:
		branch = treeFromPlug( node + "." + i)
		tree.addChild(branch)
	return tree

def isNode(target):
	"""copied to avoid dependency"""
	if "." in target: return False
	return cmds.objExists(target)

def isPlug(target):
	"""returns true for format pCube1.translateX"""
	test = False
	try:		target = str(target)
	except:		return False

	if not "." in target: return False
	return cmds.objExists(target)

def plugHType(plug):
	"""returns either leaf, array or compound"""
	if not isPlug(plug): return None
	node, attr = tokenisePlug(plug)

	mPlug = getMPlug(plug)
	if mPlug.isArray:
		return "array"
	elif mPlug.isCompound:
		return "compound"
	else:
		return "leaf"
	#
	# try:
	# 	found = cmds.attributeQuery(attr, node=node, listChildren=True)
	# 	if found: return "compound"
	# except:
	# 	pass
	#
	# if "[" in plug:
	# 	return "leaf"
	# return "leaf"


def getMPlug(plugName):
	sel = om.MSelectionList()
	sel.add(plugName)
	return sel.getPlug(0)

def getMObject(node):
	sel = om.MSelectionList()
	sel.add(node)
	return sel.getDependNode(0)


"""
con(leafA, leafB)
fine

con(compoundA, leafB)
decompose into list
con([cAx, cAy, cAz], leafB)
truncate to shortest?
con([cAx], leafB)

con(leafA, compoundB)
con(leafA, [cBx, cBy])

con([a, b, c], [x, y, z, w])
con([a, b, c], [x, y, z])


"""

def con(a, b, f=True):
	"""let's try this again
	single to compound -> single connected to all compound

	"""
	source = a

	if b[-1] == "]": # assume already defined
		dest = b
	elif plugHType(b) == "array":
		#dest = getNextAvailablePlug(b)
		bMPlug = getMPlug(b)
		dest = getNextAvailablePlug(bMPlug)

	elif plugHType(a) == "compound" and plugHType(b) == "compound" :
		# be safe against weird eval issues
		for src, dest in zip(unrollPlug(a), unrollPlug(b)):
			con(src, dest, f)
		return

	elif plugHType(b) == "compound":
		for i in unrollPlug(b):
			con(a, i, f)
		return
	else: dest = b
	#print "source {} dest {}".format(source, dest)
	cmds.connectAttr(source, dest, f=f)
	"""upgrade to om if speed becomes painful"""

def con2(a, b, f=True):
	""" attempt to be less powerful """
def con3(a, b, f=True):
	"""NOT POWERFUL ENOUGH
	we assume that plugs passed as strings have not been processed yet
	"""
	targets = [a, b]
	for i in targets:
		if isinstance(i, basestring):
			tree = treeFromPlug(i)



def conOrSet(a, b, f=True):
	"""connects plug to b if a is a plug,
	sets static value if not"""
	if isPlug(a):
		con(a, b, f)
	elif isinstance(a, tuple):
		if plugHType(b) == "compound":
			for i, val in enumerate(a):
				conOrSet(val, unrollPlug(b, returnLen=len(a))[i] )

	else:
		setAttr(b, attrValue=a)

# def getChildren(plug)

def breakConnections(target, source=True, dest=True):
	"""ed smash"""
	if isNode(target):
		for i in cmds.listAttr(target):
			breakConnections(target+"."+i, source, dest)
		return

	tree = treeFromPlug(target)
	for target in tree.allBranches():
		target = target.name
		if isPlug(target):
			test = cmds.listConnections(target, plugs=True, s=source, d=dest)
			if test:
				for i in test:
					try:
						cmds.disconnectAttr(target, i)
					except:
						cmds.disconnectAttr(i, target)


# functions for using string attributes like keys in dictionary
def addTag(tagNode, tagName, tagContent=None, tagSuffix=False):
	tagName = tagName + "_tag" if tagSuffix else tagName
	if not tagName in cmds.listAttr(tagNode):
		cmds.addAttr(tagNode, ln=tagName, dt="string")
	if tagContent:
		# tag content can be anything, keep track of it yourself
		try:
			cmds.setAttr(tagNode + "." + tagName, tagContent, type="string")
		except:
			pass
	return tagNode+"."+tagName

def edTag(tagNode):
	# more tactile to have a little top tag
	happyList = [
		":)", ":D", ".o/", "^-^", "i wish you happiness",
		"bein alive is heckin swell!!!", "it's a beautiful day today",
		"we can do this", "you matter"
	]
	ey = random.randint(0, len(happyList) - 1)
	addTag(tagNode, tagName="edTag", tagContent=happyList[ey])
	cmds.setAttr(tagNode + ".edTag", l=True)

def checkTag(tagNode, tagName, tagContent):
	# checks if a node has a specific edTag
	testList = cmds.listAttr(tagNode, string="edTag")
	if testList:
		return True
	else:
		return False

def setTagsFromDict(tagNode, tagDict):
	for k, v in tagDict.iteritems():
		addTag(tagNode, k, v)

def getDictFromTags(tagNode):
	returnDict = {}
	for i in cmds.listAttr(tagNode):
		if "_tag" in i:
			tagName = i.split("_tag")[0]
			tagContent = cmds.getAttr(tagNode+"."+i)
			returnDict.update({tagName : tagContent})
	return returnDict

def listWithTagContent(searchNodes=None, searchTag="", searchContent=""):
	found = []
	for i in searchNodes:
		searchList = cmds.listAttr(i, string="*_tag")
		for n in searchList:
			if searchContent in cmds.getAttr(i+"."+n):
				found.append(i)
	return found


def getTag(tagNode, tagName=None):
	# retrieves specific tag information, or lists all of it
	if tagName:
		gotTag = cmds.getAttr(tagNode + "." + tagName)
	else:
		gotTag = cmds.listAttr(tagNode, string="*tag")
	return gotTag

def removeTag(tagNode, tagName=None):
	search = tagName if tagName else "*_tag"
	tags = cmds.listAttr(tagNode, string=search)
	for i in tags:
		cmds.deleteAttr(tagNode+"."+i)

BUILT_ATTR = "node_built"
def tagAsBuilt(node):
	"""used in conjunction with the listing principle
	to tell if a node needs to be reconstructed or not"""
	addAttr(node, attrName=BUILT_ATTR, dv=1, dt="bool")

def isBuilt(node):
	""" seriously what does this do """
	return BUILT_ATTR in cmds.listAttr(node)


def setHidden(plug, state=True):
	cmds.setAttr(plug, cb=state)

def setLocked(plug, state=True):
	try:
		cmds.setAttr(plug, locked=state)
	except:
		print "unable to lock attr {}".format(plug)


def addUntypedAttr(node, attrName="untypedAttr"):
	""" testing api methods for this, may supercede cmd calls """
	mfnTyped = om.MFnTypedAttribute()
	aTypedObj = mfnTyped.create( attrName, attrName, om.MFnData.kAny) # kAny
	nodeObj = getMObject(node)
	mfnDep = om.MFnDependencyNode(nodeObj)
	mfnDep.addAttribute(aTypedObj)
	return node + "." + attrName


def addAttr(target, attrName="newAttr", attrType="float", parent=None,
            keyable=True, **kwargs):
	"""wrapper for more annoying attr types like string
	returns plug"""
	if parent:
		if not target in parent:
			parent = target + "." + parent
		parent = ".".join(parent.split(".")[1:])
		kwargs.update({"parent" : parent})
		#print "parent is {}".format(parent)

	# check if already exists
	attrName = kwargs.get("ln") or attrName
	if not "ln" in kwargs: kwargs["ln"] = attrName
	if attrName in cmds.listAttr(target):
		return target+"."+attrName

	if attrType == "int" : attrType = "long"
	dtList = ["string", "nurbsCurve", "mesh"]
	if attrType in dtList:
		plug = cmds.addAttr(target, dt=attrType, keyable=True,
		                    **kwargs)
	else:
		plug = cmds.addAttr(target, at=attrType, keyable=True,
		                    **kwargs)
		# if you know the logic behind at vs dt, please contact me
	# contact me urgently
	if parent:
		return parent + "." + attrName
	return target+"."+attrName

def getAttr(*args, **kwargs):
	"""J U S T I N C A S E"""
	return cmds.getAttr(*args, **kwargs)


def makeAttrsFromDict(node, attrDict, parent=None):
	"""creates compound hierarchies from a dict
	:param attrDict : dict
	:param parent : string
	(compound plug)
	{"parent" : {
		"children" : { # sad times
			"mid" : {
				"children" : {
					"child" : { "dt" : "nurbsCurve"}
					}
				},
				"other" : { "dt" : "float",
							"min" : 0 }
					}"""
	"""the syntax including "children" key is clunky, but it's most explicit
	and futureproof for array attributes"""
	for k, v in attrDict.iteritems():
		if v.get("children"): # it's a compound
			parent = addAttr(node, attrName=k, attrType="compound",
			                 nc=len(v["children"].keys()))
			makeAttrsFromDict(node, v["children"], parent=parent)
		elif v.get("dt"): # it's a normal attribute
			kwargs = {nk : nv for nk, nv in v.iteritems() if nk != "dt"}
			addAttr(node, attrName=k, attrType=v["dt"], parent=parent, **kwargs)

def copyAttr(sourcePlug, targetNode, newName=None, driveOriginal=True):
	"""currently for use only with simple attributes
	intended to allow shuffling of attributes out of a network
	on to controls
	copyAttr( someRandomNode.selector, ctrl, newName=parametreA ) """
	sourceNode, sourceAttr = tokenisePlug(sourcePlug)
	cmds.copyAttr( sourceNode, targetNode,
	               attribute=[sourceAttr], values=True)
	# until i get the proper procedural way working
	if not newName : newName = sourceAttr
	val = getAttr(sourcePlug)
	newAttr = addAttr(targetNode, attrName=newName)
	setAttr(newAttr, val)
	if driveOriginal:
		con(targetNode + "." + newName, sourcePlug)
	return newAttr
	# if newName:
	# 	renameAttr(targetNode + "." + sourceAttr, newName)
	# else: newName = sourceAttr
	# plug = targetNode + "." + newName
	# setAttr(plug, channelBox=True, keyable=True)



def renameAttr(targetPlug, newName="newAttr"):
	cmds.renameAttr(targetPlug, newName)
	node, attr = tokenisePlug(targetPlug)
	return node + "." + newName





INTERFACE_ATTRS = { # attribute templates for io network nodes
	"0D" : {"dt" : "matrix"},
	"1D" : {"children" : {
		"mainCurve" : {"dt" : "nurbsCurve"},
		"upCurve" : {"dt" : "nurbsCurve"}}},
	"2D" : {"dt" : "mesh"},
	"int" : {"dt" : "long"},
	#"message" : {"dt" : "message"}
	#ideally there would be a much closer link between this system and abstract attrs
	# give me a minute
	}

def setAttr(targetPlug, attrValue=None, absNode=None, **kwargs):
	"""similar wrapper for setAttr dealing with strings, matrices, etc
	absNode allows passing absoluteNode where performance is important"""
	if not attrValue:
		cmds.setAttr(targetPlug, **kwargs)

	#print "isPlug {} {}".format(targetPlug, isPlug(targetPlug))
	if not isPlug(targetPlug):
		raise RuntimeError("target plug {} does not exist".format(targetPlug))

	#print "plug {} hType {}".format(targetPlug, plugHType(targetPlug) )

	op = kwargs.get("relative")
	if op:
		"""increment attr value rather than set it"""
		print "setting relative"
		operators = ("+", "-", "*", "/")
		operator = op if op in operators else "+"
		base = getAttr(targetPlug)
		attrValue = eval("{} {} {}".format(base, operator, attrValue) )
		kwargs.pop("relative")

	elif isinstance(attrValue, basestring):
		# check for enum:
		#print "plug type is {}".format(plugType(targetPlug))
		if plugType(targetPlug) == "enum":
			setEnumFromString(targetPlug, attrValue)
		else:
			#cmds.setAttr(targetPlug, attrValue, type="string")
			_setAttrSafe(targetPlug, attrValue, type="string")
		return

	elif plugHType(targetPlug) == "compound":
		if isinstance(attrValue, (tuple, list)):
			""" catch those fun times when you get a value like [ ( 1.0, ) ] """
			attrValue = python.flatten(attrValue)
			#cmds.setAttr(targetPlug, *attrValue)
			_setAttrSafe(targetPlug, *attrValue)
			return

		# this is used to specify one value for a multi attr
		targets = unrollPlug(targetPlug)
		for i in targets:
			setAttr(i, attrValue=attrValue)
		return

	else:
		#cmds.setAttr(targetPlug, attrValue, **kwargs)
		_setAttrSafe(targetPlug, attrValue, **kwargs)

def _setAttrSafe(*args, **kwargs):
	""" THIS close to catching errors when setting connected attributes """
	try:
		cmds.setAttr(*args, **kwargs)
	except Exception as e:
		print("error in cmds.setAttr with args {}, kwargs {}".format(args, kwargs))
		print(e)

def setAttrsFromDict(attrDict, node=None):
	"""expects dict of format {"attr" : value}"""
	for k, v in attrDict.iteritems():
		plug = node+"."+k if node else k
		setAttr(plug, v)

def setEnumFromString(plug, value):
	"""usually the index of an enum entry, """
	node, attr = tokenisePlug(plug)
	enumList = getEnumEntries(node, attr)
	if not value in enumList:
		raise RuntimeError("invalid enum value {} for attr {} \n"
		                   "valid values are {}".format(
			value, plug, enumList ))
	cmds.setAttr(plug, enumList.index(value))
	#_setAttrSafe(plug, enumList.index(value))

def getEnumEntries(node, attr):
	""" there are terrible things here """
	enumString = cmds.attributeQuery(attr, node=node, listEnum=True)[0]
	enumList = enumString.split(":")
	for i, n in enumerate(enumList):
		if "=" in n: # the horrors
			enumList[i] = n.split("=")[0]
	enumList = [ i[0].lower() + i[1:] for i in enumList]
	return enumList

def tokenisePlug(plug):
	"""atomic to get node and attr from plug"""
	#print ""
	attr = ".".join(plug.split(".")[1:])
	node = plug.split(".")[0]
	#print "node is {}, attr is {}".format(node, attr)
	return node, attr

def plugType(plug):
	"""returns string type for plugs"""
	# attr, node = tokenisePlug(plug)
	return cmds.getAttr(plug, type=True)

def getEnumValue(plug):
	"""current enum value as string"""
	return cmds.getAttr(plug, asString=True)

def getImmediateNeighbours(target, source=True, dest=True, wantPlug=False):
	"""returns nodes connected immediately downstream of plug, or all of node"""
	nodeList = []
	if isNode(target):
		print "node target {}".format(target)
		for i in cmds.listAttr(target):
			nodeList += getImmediateNeighbours(i)
	else:
		plugs = cmds.listConnections(target, plugs=True, source=source,
		                             destination=dest)
		if not plugs:
			return []
		for i in plugs:
			nodeList.append((i.split(".")[0], i)) #node, plug

	if wantPlug:	found = [i[1] for i in nodeList if isPlug(i[1])]
	else:	found = [i[0] for i in nodeList if isNode(i[0])]
	#else: found = nodeList

	return found

def getDrivingPlug(plug):
	plugs = cmds.listConnections(plug, plugs=True, source=True, dest=False)
	if not plugs:
		return []
	return [i for i in plugs if i != plug][0]

def getImmediateFuture(target, wantPlug=False):
	return getImmediateNeighbours(target, source=False, dest=True,
	                              wantPlug=wantPlug)

def getImmediatePast(target, wantPlug=False):
	return getImmediateNeighbours(target, source=True, dest=False,
	                              wantPlug=wantPlug)

def makeMutualConnection(startNode, endNode, attrType="string",
                         startName="start", startContent=None,
                         endName="end"):
	"""base function for connecting two nodes"""
	startPlug = addAttr(startNode, attrName=startName, attrType=attrType)
	if startContent:
		setAttr(startPlug, startContent)
	endPlug = addAttr(endNode, attrName=endName, attrType=attrType)
	con(startPlug, endPlug)

def makeStringConnection(startNode, endNode,
						 startName="start", endName="end"):
	"""adds a string connection between two nodes"""
	makeMutualConnection(startNode, endNode, attrType="string",
	                     startName=startName, endName=endName)


def findPlugSource(startPlug):
	"""walk the graph backwards from an input plug
	until we find a plug without an input
	used to trace back control ui nodes"""
	stepBack = getDrivingPlug(startPlug)
	if not stepBack: # no driving plug found
		return stepBack
	return findPlugSource(stepBack)

def getTransformPlugs(node, t=True, r=True, s=True):
	"""returns list of plugs for specified node
	no more loops"""
	plugs = []
	mapping = {"translate" : t, "rotate" : r, "scale" : s}
	for i in [k for k, v in mapping.iteritems() if v]:
		for n in "XYZ":
			plugs.append(node + "." + i + n)
	return plugs

def unrollPlug(plug, returnLen=-1):
	"""unrolls compound plug returning list of its children,
	and either curtails or fills in None up to length"""
	if not plugHType(plug) == "compound" :
		return [plug]
	node, attr = tokenisePlug(plug)
	foundAttrs = cmds.attributeQuery(attr, node=node, listChildren=True)
	found = [node + "." + i for i in foundAttrs]
	return found

def getNextAvailablePlug(arrayPlug):
	"""gets the first free index for an array attribute"""
	if isinstance(arrayPlug, om.MPlug):
		length = arrayPlug.numElements()
		print("length {}".format(length))
		name = arrayPlug.partialName( includeNodeName=True,
		                              useFullAttributePath=True)
		baseName = "[".join(name.split("[")[:-1]) or name
		return baseName + "[{}]".format(length)

	length = cmds.getAttr(arrayPlug, size=True)
	print("length {}".format(length))
	if arrayPlug[-1] == "]" :
		arrayPlug = "[".join( arrayPlug.split("[")[:-1] )
	return arrayPlug+"[{}]".format(length)

def getNextAvailableIndex(arrayPlug):
	length = cmds.getAttr(arrayPlug, size=True)
	return length


# class ArgParse(object):
# 	"""experimental context handler to control creation and deletion
# 	of proxy nodes for functions."""



