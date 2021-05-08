# """legit developers have test suites right
# maybe we should do that
# """
# from edRig import scene
#
# testFuncs = []
#
# def test(func):
# 	"""small decorator to keep tests in line
# 	this could be more efficiently done - roll this
# 	principle back to a lib python class if we need to add functions
# 	to a catalogue again"""
# 	testFuncs.append(func)
# 	#print "outer func {}".format(func)
# 	def wrapper():
# 		scene.newScene()
# 		return func()
# 	return wrapper
#
#
