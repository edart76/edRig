
""" print the python script necessary to recreate selected node """
import hou

def run():
	node = hou.selectedNodes()[-1]
	fnName = "create_" + node.name()
	s = node.asCode(function_name=fnName, brief=True)
	fp = __file__[:-2] + "txt"
	with open(fp, "w") as f:
		f.write(s)