""" interfacing with video files using ffmpeg """
import os, sys, subprocess
from edRig import ROOT_PATH

REF_PATH = os.path.join(ROOT_PATH, "ref", "")


def convertImagesToVideo(folder, nameFormat="mayaPlayblast",
                         framerate=24, framePadding=3):
	""" assumes that all images in folder are to be converted """

	spec = os.listdir(folder)[0] # example file
	imgName = spec.split(".")[0]
	imgFormat = spec.split(".")[-1]

	outputPath = os.path.join( *folder.split("\\")[:-1])

	if nameFormat == "mayaPlayblast":
		imgLookup = "{}.%0{}d.{}".format(imgName, framePadding, imgFormat)

	# cmd = "ffmpeg -r 60 -f image2 -s 1920x1080 -i pic%04d.png " \
	#       "-vcodec libx264 -crf 25  -pix_fmt yuv420p test.mp4"
	# r framerate, f mode, s resolution, i imageName,
	# crf quality, pix_fmt pixelFormat, outputFile

	cmd = "ffmpeg -y -r {} -f image2 -i {} -vcodec libx264 -crf 15 {}\\{}_output.mp4".format(
		framerate, imgLookup, outputPath, imgName
	)



	print("cmd")

	print( cmd )
	print( folder)

	os.chdir(folder)

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

	convertImagesToVideo(folder)
