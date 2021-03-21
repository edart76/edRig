
""" functions for working with houdini apprentice """


from PIL import Image


testDir = r"F:\all_projects_desktop\houdini\training\images\croptest"

def cropWatermark(image):
	""" given Image,
	crop bottom proportion of image to remove watertag

	first note down the top left pixel of watermark for various resolutions
	OR
	just always use 1280x720 camera resolution and adjust resolution with pil

	top left is (1024, 644)
	:returns Image.Image
	"""


	width = image.width
	height = image.height
	rect = (0, 0, width, 644)
	cropped = image.crop( rect)

	return cropped


if __name__ == '__main__':

	testFile = testDir + r"\testA.jpg"
	print(testFile)
	i = Image.open(testFile, mode="r") #type: Image.Image
	#i = Image.Image(testFile) #type: Image.Image
	cropped = cropWatermark(i)

	cropped.save(testDir + "/cropped.png")

