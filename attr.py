# lib for adding and modifying attributes
import random
from maya import cmds
import maya.api.OpenMaya as om

dimTypes = {
	"0D" : ("matrix",),
	"1D" : ("nurbsCurve", "bezierCurve"),
	"2D" : ("nurbsSurface", "mesh")
}

def isNode(target):
	"""copied to avoid dependency"""
	if "." in target: return False
	return cmds.objExists(target)

def isPlug(target):
	"""returns true for format pCube1.translateX"""
	if not isinstance(target, basestring): return False
	if not "." in target: return False
	return cmds.objExists(target)

def plugHType(plug):
	"""returns either leaf, array or compound"""
	node, attr = tokenisePlug(plug)
	# querying on common scale attr gives multi false, children list

	try:
		found = cmds.attributeQuery(attr, node=node, listChildren=True)
		if found: return "compound"
	except:
		pass

	if "[" in plug:
		return "leaf"
	return "leaf"
	# print "node {}, attr {}".format(node, attr)
	# if not cmds.attributeQuery(attr, node=node, multi=True):
	# 	return "leaf"

	# else: return "array"  # too complex, too much obfuscation

	return "leaf"


def getMPlug(plugName):
	sel = om.MSelectionList()
	sel.add(plugName)
	return sel.getPlug(0)

def con(a, b, f=True):
	"""let's try this again"""
	source = a
	#print "plugtype {}".format(plugHType(b))
	if plugHType(b) == "array":
		dest = getNextAvailableIndex(b)

	elif plugHType(a) == "compound" and plugHType(b) == "compound" :
		dest = b

	elif plugHType(b) == "compound":
		for i in unrollPlug(b):
			con(a, i, f)
	else: dest = b
	#print "source {} dest {}".format(source, dest)
	cmds.connectAttr(source, dest, f=f)
	"""upgrade to om if speed becomes painful"""

def conOrSet(a, b, f=True):
	"""connects plug to b if a is a plug,
	sets static value if not"""
	if isPlug(a):
		con(a, b, f)
	else:
		setAttr(b, attrValue=a)

# def getChildren(plug)

def breakConnections(target, source=True, dest=True):
	"""ed smash"""
	if isNode(target):
		for i in cmds.listAttr(target):
			breakConnections(target+"."+i, source, dest)
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
	if attrName in cmds.listAttr(target):
		return target+"."+attrName

	if attrType == "int" : attrType = "long"
	dtList = ["string", "nurbsCurve"]
	if attrType in dtList:
		plug = cmds.addAttr(target, ln=attrName, dt=attrType, keyable=True,
		                    **kwargs)
	else:
		plug = cmds.addAttr(target, ln=attrName, at=attrType, keyable=True,
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
		else: cmds.setAttr(targetPlug, attrValue, type="string")
		return

	elif plugHType(targetPlug) == "compound":
		if isinstance(attrValue, (tuple, list)):
			"""try everything"""
			cmds.setAttr(targetPlug, *attrValue)
			return

		targets = unrollPlug(targetPlug)
		for i in targets:
			setAttr(i, attrValue=attrValue)
		return

	else:
		cmds.setAttr(targetPlug, attrValue, **kwargs)

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

def getNextAvailableIndex(arrayPlug):
	"""gets the first free index for an array attribute"""
	length = cmds.getAttr(arrayPlug, size=True)
	if arrayPlug[-1] == "]" :
		arrayPlug = "[".join( arrayPlug.split("[") )
	return arrayPlug+"[{}]".format(length)



# class ArgParse(object):
# 	"""experimental context handler to control creation and deletion
# 	of proxy nodes for functions."""



