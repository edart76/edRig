""" placed in edRig for convenience -
basic backup automation system
iterates over folders from root, finding all files including 'v001'
or similar in title
copies last two versions and containing folder structure to temp,
zips file to compress, dates and moves file to backup location

no way of telling what has changed - could maybe save files against timestamp?
need to investigate
"""


import os, shutil, pprint

from edRig.pipeline import getLatestVersions, sortVersions

blacklist = "backup"

blacklistExtensions = [
	".git",
	".zip",
	".h",
	".py",
	".cpp",
	".rar",
	".bin",
	".msi",


]


def makeBackup( rootFolder, outputFilePath, test=False):

	"""iterate recursively over all files and folders
	unless containing blacklist items

	COPY ENTIRE TREE first
	then iterate and delete files not needed
	"""

	paths = [] # stupid basic progress reporting

	if os.path.exists(outputFilePath):
		#print "already exists"
		#os.rmdir(outputFilePath)
		shutil.rmtree(outputFilePath)
		#return

	#shutil.copytree(rootFolder, outputFilePath)

	files = []
	treeDict = {}
	for x in os.walk(rootFolder):
		# ( fullFolderPath, subFolderNames, files
		localFiles = [i for i in x[2] if not any([
			i.endswith(n) for n in blacklistExtensions])]
		if not localFiles:
			continue
		#saves = getLatestVersions(localFiles)
		versions = sortVersions(localFiles)
		if not versions:
			continue
		# 	returns dict of {fileTag : {versionNumber :
		#       (description, full file name) } }

		saves = []
		for title, data in versions.items():
			maxVersion = max(data.keys())
			saves.append(data[maxVersion][1])

		# if "ophelia" in x[0]:
		# 	pprint.pprint(versions)
		# 	print(saves)

		treeDict[x[0]] = saves
		#print
		#print "saves {}".format(saves)

		fullDirPath = x[0]
		destDirPath = fullDirPath.replace(rootFolder, outputFilePath)

		os.makedirs(destDirPath)

		for i in saves:

			fullFilePath = fullDirPath + "\\" + i
			destFilePath = fullFilePath.replace(rootFolder, outputFilePath)
			# shutil.copyfile(fullPath, destPath)
			paths.append( (fullFilePath, destFilePath))
			if test:
				#print("source {}".format(fullFilePath))
				#print("dest   {}".format(destFilePath))
				#print("")
				continue

	n = len(paths)
	nSegment = n / 100
	nCurrent = 0
	percentDone = 0.0
	for i, val in enumerate(paths):
		if nCurrent == nSegment:
			percentDone = percentDone + 10.0
			print(("at {} percent".format(percentDone)))
			nCurrent = 0
		else:
			nCurrent = nCurrent + 1


		try:
			#shutil.copy2(fullFilePath, destFilePath)
			shutil.copy2(val[0], val[1])
		except:
			print(( "error encountered copying file {}".format(val[0])))
			continue




if __name__ == "__main__":

	""" run test backup """

	rootPath = "F:/all_projects_desktop"
	outputPath = r"F:\autoBackup\v011"

	# rootPath = r"F:\all_projects_desktop\testRoot"
	# outputPath = r"F:\all_projects_desktop\testBackup"



	makeBackup( rootPath, outputPath, test=False )





