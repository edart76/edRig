""" interfacing with video files using ffmpeg """
import os, sys, subprocess
from edRig import ROOT_PATH

REF_PATH = os.path.join(ROOT_PATH, "ref", "")


def convertImagesToVideo(folder, name=None, imgFormat=None, nameFormat="mayaPlayblast",
                         framerate=24, framePadding=3):
	""" assumes that all images in folder are to be converted """

	spec = os.listdir(folder)[0] # example file
	imgName = name or spec.split(".")[0]
	imgFormat = imgFormat or spec.split(".")[-1]

	outputPath = os.path.join( *folder.split("\\")[:-1])
	outputPath = folder

	if nameFormat == "mayaPlayblast":
		imgLookup = "{}%0{}d.{}".format(imgName, framePadding, imgFormat)
		#imgLookup = "*".format(imgName, framePadding, imgFormat)

	# cmd = "ffmpeg -r 60 -f image2 -s 1920x1080 -i pic%04d.png " \
	#       "-vcodec libx264 -crf 25  -pix_fmt yuv420p test.mp4"
	# r framerate, f mode, s resolution, i imageName,
	# crf quality, pix_fmt pixelFormat, outputFile

	cmd = "ffmpeg -y -r {} -f image2 -i {} -vcodec libx264 -crf 15 {}\\{}output.avi".format(
		framerate, imgLookup, outputPath, imgName
	)

	# cmd = "ffmpeg -y -r {} -f image2 -vcodec libx264 -crf 15 -pattern_type glob -i '*' output.mp4".format(
	# 	framerate,
	# )

	print("cmd")

	print( cmd )
	print( folder)

	os.chdir(folder)

	os.system(cmd)

	# process = subprocess.Popen( cmd.split(" "),
	#                             stdout=subprocess.PIPE,
	#                             stderr=subprocess.PIPE)
	# while True:
	# 	output = process.stdout.readline().strip()
	# 	if output:
	# 		print(output)
	# 	returnCode = process.poll()
	# 	if returnCode is not None: # process finished
	# 		break
	# return returnCode


if __name__ == '__main__':

	folder = os.path.join(ROOT_PATH, "cait\progress\impressionism\subdued_lit",)
	folder = r"F:\all_projects_desktop\base_mesh\pres\images_v1"
	convertImagesToVideo(folder, name="_", imgFormat="png")
	# os.chdir(folder)
	#
	# cmd = "ffmpeg -y -r 24 -f image2 -vcodec libx264 -crf 15 -pattern_type glob -i '*' output.mp4"
	# cmd = "ffmpeg -framerate 25 -pattern_type glob -i '*.png' output.avi"

	# os.system(cmd)