
from edRig import hou
import re

""" functions to support vex files """

ARRAYTYPES = ("int", "float", "vector", "string")

def templateReplaceString(sourcestring, targetstring,
                          templateToken, templateValues):
	""" templates marked vex functions to work on desired types """
	for value in templateValues:
		targetstring += sourcestring.replace(templateToken, value)
	return targetstring

