"""general lib for nifty python things like decorators and debugs"""
from __future__ import print_function
import inspect,importlib, pprint



# thank you code recipe 576925
def caller():
	"""whatever called this"""
	return inspect.getouterframes(inspect.currentframe())[1][1:4]
def callee():
	"""this specific function
	:returns (modulePath, line, funcname)"""
	return inspect.getouterframes(inspect.currentframe())[2][1:4]

def debug(var):
	"""prints the name and value of var, in the scope it comes from
	eg a = 23, debug (a) - 'a is 23' """
	callerFrame = inspect.stack()[1][0]
	name = [k for k, v in callerFrame.f_locals.iteritems() if v is var][0]
	print("{} is {}".format(name, pprint.pformat(var)))
	return name # part of me is sad this isn't more crazy

def outerVars():
	"""returns a dict of variable names from the outer scope of the call
	used mainly to add actions to classes because decorators drive me mad"""
	callerFrame = inspect.stack()[1][0]
	return callerFrame.f_locals




# move the module import here from pipeline