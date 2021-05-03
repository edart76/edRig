
import string, re, fnmatch

def searchReplaceMain(stringList, searchTokens, replaceTokens,
                      preserveCase=True,
                      stripTrailDigits=True):
	"""main function called by tool"""
	result = []
	for s in stringList:
		result.append(searchReplace(s, searchTokens, replaceTokens,
		              preserveCase=preserveCase,
		                            stripTrailDigits=stripTrailDigits))
	return result


def searchReplace(s, searchTokens, replaceTokens,
                  preserveCase=True,
                  stripTrailDigits=True):
	""" individual search replace operation
	simple for now
	:type s : str"""
	result = s
	for search, replace in zip(searchTokens, replaceTokens):
		result = result.replace(search, replace)
	if stripTrailDigits:
		result = result.rstrip(string.digits)

	return result







