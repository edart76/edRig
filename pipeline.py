# functions for manipulation of pipeline folder structures
"""all the file management and asset stuff is very very shaky
it's probably not ready for use outside of helping manage tesserae"""
import os, sys, importlib, pprint, io, tempfile
import re

from edRig.lib.python import AbstractTree

from edRig import ROOT_PATH, COMMON_PATH, cmds
#from maya import cmds # hurts but there's no point in a separate module yet


defaultFolders = ["models", "materials", "ref", "assemblyData"] # create these dynamically as required
defaultFiles = [] # maybe
coreFolders = ["archive",]
coreFiles = ["config", "asset", "version",]
defaultExtensions = [".txt", ".tes", ".json", ".tp"]

dataFolder = "F:/all projects desktop/common/edCode/edRig/data/"
tempPath = dataFolder + "tempData"


class FilePathTree(str):
	"""structure for walking and searching directories
	easily and safely
	"""
	def __init__(self, path):
		#print "filePathTree path is {}".format # works
		if isinstance(path, FilePathTree):
			path = path.path
		super(FilePathTree, self).__init__(path)
		if self.isPath(path):
			self.path = path
		else:
			raise RuntimeError("path {} does not exist".format(path))
		self.hType = self.getHType(self.path)

	# string behaviour
	def __add__(self, other): # doesn't account for adding filepathtrees hmmm
		return self.path.__add__(other)
	def __iadd__(self, other):
		return self.path.__iadd__(other)
	def __len__(self):
		return len(self.path)

	def __repr__(self):
		return self.path

	def __str__(self):
		return self.path

	def __getitem__(self, item):
		"""alternative to look up string variables
		returns content of a text file when retrieved"""
		if item in self.__dict__:
			return self.__dict__[item]
		elif item in str.__dict__:
			return str(self).__dict__[item]
		else:
			if not self.hType == "dir":
				return None
			elif item in self.children:
				if self.isFile(self.path+"/"+item):
					return
				return FilePathTree(self.children[item])
			elif self.nameFromPath(item) in self.children:
				return FilePathTree(self.children[self.nameFromPath(item)])
			else:
				return None

	@property
	def parent(self):
		return FilePathTree("/".join(self.path.split("/")[:-1]))

	@property
	def children(self):
		return self.listChildren()

	@property
	def name(self):
		return self.nameFromPath(self.path)

	def listChildren(self):
		"""lists current files in directory in dict of names and paths
		we don't build a whole tree, because that could get REAL slow"""
		children = {}
		if self.hType == "leaf":
			return None
		elif self.hType == "dir":
			for i in os.listdir(self.path):
				newPath = self.path+"/"+i
				#print "os listdir is {}".format(i)
				#print "newPath is {}".format(newPath)
				#print ""
				children[self.nameFromPath(newPath)] = FilePathTree(newPath)
				#children[self.nameFromPath(newPath)] = newPath
			#print "this is a dir"
		#print "children are {}".format(children)
		return children

	@property
	def files(self):
		"""all child files at current level, not directories"""
		files = []
		for i in self.children.values():
			if self.isFile(i):
				files.append(i)
		return files

	def makeChildFolder(self, name):
		newPath = self.path+"/"+name
		if len(self.getLevels(name)) > 1:
			os.makedirs(newPath)
			"""multiple nested dir creation not yet properly supported"""
			return FilePathTree(newPath)

		if name in self.children:
			return self[name]
		elif self.isPath(newPath):
			return FilePathTree(newPath)
		else:
			try:
				os.mkdir(newPath)
			except:
				print "failed to create folder {}".format(name)
			return FilePathTree(newPath)

	def makeChildFile(self, name, suffix=".txt"):
		f = open(self.path+"/"+name+suffix, "w+")
		f.close()

	def stripParentPath(self, path):
		if not self.path in path:
			return path
		return path.replace(self.path, "")

	@staticmethod
	def stripExt(path):
		"""removes filetype extension from path, if it exists
		if you have more than one dot in a file name this won't go well"""
		if "." in path:
			path = "/".join(path.split(".")[:-1])
		return path

	@staticmethod
	def getLevels(path):
		return path.split("/")

	@staticmethod
	def stripPath(path):
		"""returns only the 'file' part of file path"""
		return path.split("/")[-1]

	@staticmethod
	def nameFromPath(path):
		return FilePathTree.stripExt(FilePathTree.stripPath(path))

	@staticmethod
	def getHType(path):
		if os.path.isfile(path):
			return "leaf"
		elif os.path.isdir(path):
			return "dir"

	@staticmethod
	def isPath(path):
		return os.path.exists(path)

	@staticmethod
	def isDir(path):
		return os.path.isdir(path)

	@staticmethod
	def isFile(path, ext=False):
		if isinstance(path, basestring):
			if not ext:
				path = FilePathTree.stripExt(path)
				return any([FilePathTree.isFile(path+i, ext=True) for i in defaultExtensions])
			return os.path.isfile(path)
		elif isinstance(path, FilePathTree):
			return os.path.isfile(path.path)

	def read(self):
		if self.hType == "dir":
			return None
		# would be nice to provide sameless access to file info

	def copyTo(self):
		"""copies filetree to new location?"""

def getTempFile(usage="temp"):
	""""""


def ioinfo(name="", mode="in", info=None, path=None):
	# read and write generic info to and from maya
	# name is key in file dictionary
	goss = {}
	# path = checkJsonSuffix(path)
	if not path:
		return None
	if mode == "in":
		with open("{}".format(path)) as file:
			# goss = json.load(file)
			#goss = json.loads(eval(file.read()))
			goss = file.read()

		if isinstance(goss, dict):
			print "goss is dict"
			return goss

		try:
			#goss = eval(ast.literal_eval(str(goss)))
			goss = eval(goss)
		except Exception as e:
			print "ERROR in attrio reading from file {}".format(path)
			print "error is {}".format(str(e))
		#print "goss is {}".format(goss)

		return goss

	elif mode == "out":

		#file = os.open(path, "w+b")
		with open(path, "w+b") as file:
			# file.write(pprint.pformat(json.dumps(info), indent=3))
			# #file.write(pprint.pformat(info, indent=3))
			# file.write(json.dumps(pprint.pformat(info, indent=3)))
			file.write(pprint.pformat(info, indent=2))
			file.close()

	else:
		raise RuntimeError("no valid mode ('in' or 'out') to ioinfo")



def isDir(path):
	return os.path.isdir(path)

def isAsset(path):
	if not os.path.exists(str(path)):
		return False
	tree = FilePathTree(path)
	if tree["asset.txt"]:
		return True

def makeAsset(assetName=None, assetPath=None, parent=None):
	"""creates basic folder structure, including archive and config"""
	if assetName:
		path = ROOT_PATH+"/"+str(assetName)
	else:
		path = assetPath
	if not FilePathTree.isDir(path):
		os.mkdir(path)
	makeAssetStructure(path, core=True)

def checkAssetStructure(dir, core=True):
	"""checks that core structure exists"""
	for i in coreFolders:
		if not FilePathTree.isDir(dir+"/"+i):
			print "found no coreFolder {} in asset {}".format(i,
			                                                  dir)
			return False
	for i in coreFiles:
		if not FilePathTree.isFile(dir+"/"+i):
			print "found no coreFile {} in asset {}".format(i,
			                                                  dir)
			return False
	return True

def makeAssetStructure(dir, core=True, all=False):
	"""creates folders"""
	tree = FilePathTree(dir)
	for i in coreFolders:
		if not i in tree.children:
			print "making child core folder {}".format(i)
			tree.makeChildFolder(i)
	for i in coreFiles:
		if not i in tree.children:
			print "making child core file {}".format(i)
			tree.makeChildFile(i, suffix=".txt")

def getExistingAssets(checkPath=ROOT_PATH):
	"""returns file trees for all existing top-level asset folders
	return a flat list for all, regardless of asset groups"""
	assets = {}
	if not isinstance(checkPath, list):
		checkPath = [checkPath]
	for i in checkPath:
		tree = FilePathTree(i)
		for name, path in tree.children.iteritems():
			if isAsset(path):
				if isDir(path+"/components"): # check fractally for elements of asset groups
					assets.update(getExistingAssets(path+"/components"))
				assets[name.capitalize()] = path
	#print "existing assets are {}".format(assets) # works
	return assets

def safeLoadModule(mod):
	"""takes string name of module
	DEPRECATED, use lib/python/safeLoadModule"""
	# print "loading module {}".format(mod)
	module = None
	for i in sys.modules.keys():
		# if "edRig" in i: del sys.modules[i] # how about FUCKIN NO
		# if mod in i : del sys.modules[i]
		pass
	try:
		module = importlib.import_module(mod)
	except Exception as e:
		print "ERROR in loading module {}".format(mod)
		print "error is {}".format(str(e))
	return module

def renameFile(old="", new="", suffix=""):
	if suffix: # legacy, don't use this
		new = checkSuffix(new, suffix)
		old = checkSuffix(old, suffix)
	print "rename old is {}, new is {}".format(old, new)
	if os.path.exists(old):
		try:
			print "found file {}, renaming to {}".format(old, new)
			os.rename(old, new)
		except  RuntimeError("could not rename file {}".format(old)):
			pass
		except RuntimeError:
			pass

def checkSuffix(path, suffix="json"):
	"""adds selected to suffix to path if not there"""
	#if suffix in path:
	if path.endswith(suffix):
		return path
	else:
		if "." in path:
			path = "".join(path.split(".")[:-1])
		return path+"."+suffix

def writeToFile(path=None, info=None):
	"""writes selected DICT to file"""

#testPath = r'F:\\all projects desktop\common\edCode\edRig\data\ctrls\ctrlLibraryv02.ma'
def makeLegit(path):
	"""callback to be run after the scene is saved to remove student license warning
	technically i am still meant to be at university :) """

	if not os.path.exists(path):
		print "unable to legitify path {}".format(path)
		return False
	with open(path, mode="r+") as f:
		heinous = f.readlines()
		f.seek(0)
		f.truncate()
		#print "heinous is {}".format(heinous)
		#legit = [i for i in heinous if not i == 'fileInfo "license" "student";\n']

		testLines = heinous[:20]
		for i, line in enumerate(testLines):
			#print "line is " + line
			if 'fileInfo "license" "student";\n' in line:
				heinous.pop(i)
				break

		# student warning should always be at same line in file
		# print "legit is {}".format(legit)
		# f.writelines(legit)
		f.writelines(heinous)
	return True

def makeBogus(path):
	"""pretend like you're some washed-up pauper using the student version"""
	if not os.path.exists(path):
		print "unable to strip path {} of material and spiritual wealth".format(path)
		return False
	with open(path, mode="r+") as f:
		wealthy = f.readlines()
		f.seek(0)
		f.truncate()
		testLines = wealthy[:20]
		mod = True

		for i, line in enumerate(testLines):
			#print "line is " + line
			if 'fileInfo "license" "student";\n' in line:
				print "already poor lol"
				mod=False
				break
		if mod:
			wealthy.insert(11, 'fileInfo "license" "student";\n')
		f.writelines(wealthy)
	return True

def safeMayaImport(path):
	"""common import function across edRig"""
	makeLegit(path)
	cmds.file(path, i=True, type="mayaAscii",
	          defaultNamespace=True)

def safeRead(path, lines=False):
	"""simple wrapper for reading files"""
	with open(path, "r") as f:
		if lines:
			content = f.readlines()
		else:
			content = f.read()
	return content

def getMostRecentVersion(dir):
	"""returns filepath of the most recent file version in the directory,
	specified by v01, v_01 etc"""


class AssetItem(str):
	"""pythonic wrapper around assets, passed the top folder"""
	def __init__(self, path):
		super(AssetItem, self).__init__(path)
		if not isAsset(path):
			raise RuntimeError("path {} is not an asset".format(path))
		self.path = str(path)
		self.tree = FilePathTree(path)
		self.name = FilePathTree.nameFromPath(self.path)
		
	def __getitem__(self, item):
		"""alternative was writing out loads of properties"""
		print "asset {} getting item {}".format(self.path, item)
		if item in coreFiles or item in defaultFiles:
			if not self.tree[item]:
				self.tree.makeChildFile(item, ".txt")
			return self.tree[item]
		elif item in coreFolders or item in defaultFolders:
			if not self.tree[item]:
				self.tree.makeChildFolder(item)
			return self.tree[item]
		else:
			return self.__dict__[item]

	@property
	def dataPath(self):
		"""returns folder for saving data of various TilePile operations"""
		return self["assemblyData"]

TempAsset = AssetItem(ROOT_PATH+"/temp")
rootTree = FilePathTree(ROOT_PATH)

def assetFromName(name):
	asset = getExistingAssets().get(name.capitalize())
	if asset:
		return AssetItem(asset)
	return None

def reloadEdRig(tesserae=True):
	"""force reload all edRig packages
	if not tesserae, will try not to crash tesserae"""
	protecc = {"tesserae" : ("layers", "tesserae")}
	import sys
	for i in sys.modules.keys():
		if "edRig" in i:
			if not tesserae and any([n in i for n in protecc["tesserae"]]):
				continue
			else:   del sys.modules[i]


def getLatestVersions( files=None, versions=2, path=None ):
	""" looks through a set of files for those marked as versions
	returns the latest x number of files

	ONLY SUPPORTS ONE PROJECT PER FOLDER
	"""
	if path:
		files = os.listdir(path)

	allVersions = sorted([ isVersion(i) for i in files], reverse=True)
	versionMap = [ ( i, isVersion(i) ) for i in files ]
	#print "versionMap {}".format(versionMap)
	#print "allVersions {}".format( allVersions)
	if not any([ i[1] for i in versionMap ]):
		return []
	r = []
	for n in range( versions ):
		if len(allVersions) >= n:
			for f in versionMap:
				if f[1] == allVersions[0]:
					r.append( f[0] )
					versionMap.remove(f)

			allVersions.pop(0)
	return r

def isVersion(fileName):
	""" run regex (v\W*\w){1} to check for "v001" or similar
	return the version number or 0 """
	try:
		pattern = re.compile( r"(v(\d|\s)*)")
		reresult = re.findall( pattern, fileName)
		#print "re result {}".format(reresult)
		# list of tuples (matchString, index)

		tokens = [ i for i in reresult if i]
		#print "tokens {}".format(tokens)
		if not tokens:
			return 0
		#
		# digits = [i for i in tokens[0][0] if i.isdigit()]
		# print "digits {}".format(digits)

		version = int( "".join( i for i in tokens[0][0] if i.isdigit() ) )

		# print "fileName {}".format(fileName)

		#print "version {}".format(version)
		return version
	except:
		return 0


def makeBlankFile(path=tempPath):
	# just to set things up
	randomFact = "crocodiles have two aortas"
	blankDict = {"did you know ": randomFact}

	ioinfo(path=path, mode="out", info=blankDict)


def checkJsonSuffix(path):
	if ".json" in path:
		path = path.split(".json")[0]
	return path + ".json"


def checkJsonFileExists(filePath):
	##print "testPath is {}".format(filePath)
	if os.path.exists(filePath + ".json"):
		return True
	else:
		return False

def checkFileExists(filePath):
	return os.path.exists(filePath)


def convertRootPath(path, toRelative=False, toAbsolute=False):
	""" converts a path to or from a relative path to root folder
	:type path str"""
	if "ROOT" in path or toAbsolute: # relative
		return path.replace("ROOT", ROOT_PATH)
	elif ROOT_PATH in path or toRelative:
		return path.replace(ROOT_PATH, "ROOT")


def saveObjectClass(obj, regenFunc="fromDict", relative=True, uniqueKey=True):
	""" saves a module and class reference for any object
	if relative, will return path from root folder"""
	keys = [ "NAME", "CLASS", "MODULE", "regenFn" ]
	if uniqueKey: # not always necessary
		for i in range(len(keys)): keys[i] = "?" + keys[i]

	path = convertRootPath(obj.__class__.__module__, toRelative=relative)
	return {
		keys[0]: obj.__name__,
		keys[1]: obj.__class__.__name__,
		keys[2]: path,
		keys[3]: regenFunc
	}

def loadObjectClass(objData):
	""" recreates a class object from any known module """
	for i in ("?MODULE", "?CLASS"):
		if not objData.get(i):
			print("objectData {} has no key {}, cannot reload class".format(objData, i))
			return None

	module = convertRootPath( objData["?MODULE"], toAbsolute=True)
	loadedModule = safeLoadModule(module)
	try:
		newClass = getattr(loadedModule, objData["?CLASS"])
		return newClass
	except Exception as e:
		print("ERROR in reloading class {} from module {}")
		print("has it moved, or module files been shifted?")
		print( "error is {}".format(str(e)) )
		return None

def reloadAllReferences():
	""" syncs a maya scene to update all references """
	allrefs = cmds.ls( type="reference" )

	for i in allrefs:
		try:
			cmds.file( unloadReference=i)
			cmds.file( loadReference=i, lockReference=False,
			           loadReferenceDepth="all",
			           #mergeNamespacesOnClash=1, # bamboo_:bamboo_:bamboo_:...
			           groupReference=1,
			           groupName=i,
			           )
		except Exception as e:
			print(e)
			print("failed to reload reference {}".format(i))

def getScenePath():
	return cmds.file(q=True, sn=True)

def exportToObj(targetGeo=None, path=None, force=True):
	# don't know how to export other than selection
	path = checkSuffix(path, suffix="obj")
	cmds.select(targetGeo, replace=True)
	cmds.file(path, pr=1, typ="OBJexport", es=1, f=force,
	          op="groups=0; ptgroups=0; materials=0; smoothing=0; normals=0")
	cmds.select(cl=1)


