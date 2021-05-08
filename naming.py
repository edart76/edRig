"""libs for manipulating element names, getting free names etc"""

import string

def incrementName(name, currentNames=None):
	"""checks if name is already in children, returns valid one"""
	if name[-1].isdigit(): # increment digit like basic bitch
		new = int(name[-1]) + 1
		return name[:-1] + str(new)
	if name[-1] in string.ascii_uppercase: # ends with capital letter
		if name[-1] == "Z": # start over
			name += "A"
		else: # increment with letter, not number
			index = string.ascii_uppercase.find(name[-1])
			name = name[:-1] + string.ascii_uppercase[index+1]
	else: # ends with lowerCase letter
		name += "A"

	# check if name already taken
	if currentNames and name in currentNames:
		return incrementName(name, currentNames)
	print("found name is {}".format(name))
	return name

def camelCase(name):
	return name[0].lower() + name[1:]