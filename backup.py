""" placed in edRig for convenience -
basic backup automation system
iterates over folders from root, finding all files including 'v001'
or similar in title
copies last two versions and containing folder structure to temp,
zips file to compress, dates and moves file to backup location"""


import os, shutil

from edRig.pipeline import getLatestVersions

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


def makeBackup( rootFolder, outputFilePath):

	"""iterate recursively over all files and folders
	unless containing blacklist items

	COPY ENTIRE TREE first
	then iterate and delete files not needed
	"""

	if os.path.exists(outputFilePath):
		print "already exists"
		#os.rmdir(outputFilePath)
		shutil.rmtree(outputFilePath)
		#return

	#shutil.copytree(rootFolder, outputFilePath)

	files = []
	treeDict = {}
	for x in os.walk(rootFolder):
		# ( fullFolderPath, subFolderNames, files
		localFiles = [i for i in x[2] if not any([
			n in i for n in blacklistExtensions])]
		if not localFiles:
			continue
		saves = getLatestVersions(localFiles)

		if not saves:
			continue
		treeDict[x[0]] = saves
		print
		print "saves {}".format(saves)

		fullDirPath = x[0]
		destDirPath = fullDirPath.replace(rootFolder, outputFilePath)

		os.makedirs(destDirPath)

		for i in saves:

			fullFilePath = fullDirPath + "\\" + i
			destFilePath = fullFilePath.replace(rootFolder, outputFilePath)
			# shutil.copyfile(fullPath, destPath)
			try:
				shutil.copy2(fullFilePath, destFilePath)
			except:
				print "error encountered copying file {}".format(fullFilePath)
				continue


if __name__ == "__main__":

	""" run test backup """

	rootPath = "F:/all_projects_desktop"
	outputPath = r"F:\autoBackup\v001"

	# rootPath = r"F:\all_projects_desktop\testRoot"
	# outputPath = r"F:\all_projects_desktop\testBackup"

	makeBackup( rootPath, outputPath )



