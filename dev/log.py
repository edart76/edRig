

"""test logger"""

from __future__ import annotations
import typing as T
import sys, os, pathlib, json, pprint
from functools import partial
from collections import defaultdict

from PySide2 import QtCore, QtWidgets, QtGui

import logging, traceback, inspect


from tree import Tree, TreeWidget


class TreeLogger(logging.Logger):
	def __init__(self, level=logging.DEBUG):
		super(TreeLogger, self).__init__(
			name="edLog", level=level)

	def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
		print("stack info")
		print(stack_info)
		return super(TreeLogger, self)._log(
			level, msg, args, exc_info, extra, stack_info)


def log(msg):
	"""main logging function"""

"""architecture isn't too clean, separate QObject and log handler"""

class QLogObject(QtCore.QObject):
	logSignal = QtCore.Signal(dict)

class TreeLogHandler(logging.Handler):
	"""leaf trees are log messages"""
	def __init__(self,
	             level=logging.DEBUG,
	             qtParent=None):
		super(TreeLogHandler, self).__init__(level)
		self.qtParent = qtParent
		self.obj = QLogObject(parent=qtParent)
		self.logTree = Tree("logRoot", default={})
		self.logSignal = self.obj.logSignal

	def emit(self, record:logging.LogRecord):
		stack = inspect.stack()
		# filter to find frame of "_log" function in logger
		logFrame = next(filter(lambda x: x.frame.f_code is TreeLogger._log.__code__, stack))
		frameId = stack.index(logFrame) + 2
		# find active frames of interest in program
		frames = stack[frameId:]

		address = []
		branch = self.logTree
		for frame in frames[::-1]:
			address.append(frame.function)
			# append index to function name for logging from same function
			n = len(branch.branches)
			#branch = branch("{}_{}".format(frame.function, n))
			branch = branch(frame.function, default={})
			print("v", branch.v)
			print("def", branch.default)
			existing = branch.v.get("logs", [])
			branch.v["logs"] = existing + [record.msg]


		self.obj.logSignal.emit({"record" : record,
		                         "stack" : stack,
		                         "tree" : self.logTree})

	def flush(self):
		self.logTree.clear()
		self.obj.logSignal.emit({"record" : None,
		                         "stack" : [],
		                         "tree" : self.logTree})
	pass

mainLogger = TreeLogger()

mainHandler = TreeLogHandler()

mainLogger.addHandler(mainHandler)


#class LogTree(QtWidgets.QTreeWidget):
class LogTree(TreeWidget):
	# def __init__(self, parent=None):
	# 	super(LogTree, self).__init__(parent=parent)

	def receiveLog(self, data):
		tree = data["tree"] #type:Tree
		self.setTree(tree)
		# for branch in tree.allBranches():
		# 	pass

		# record = data["record"]
		# stack = data["stack"]
		# for i in stack:
		# 	#print(i)
		# 	#print(i.code_context, i.index)
		# 	pass
		# #print(data)

class LogWidget(QtWidgets.QWidget):
	def __init__(self, parent=None, handler=None):
		super(LogWidget, self).__init__(parent=parent)
		self.handler = handler #type:TreeLogHandler
		self.tree = LogTree(self, tree=self.handler.logTree)

		self.makeConnections()

		self.makeLayout()

	def makeLayout(self):
		vl = QtWidgets.QVBoxLayout(self)
		vl.addWidget(self.tree)
		self.setLayout(vl)

	def makeConnections(self):
		self.handler.logSignal.connect(self.onLogEmit)

	def onLogEmit(self, data):
		#print("data", data)
		self.tree.receiveLog(data)

def testFn():
	mainLogger.debug("main function log")

	def _inner():
		mainLogger.debug("inner function")
	_inner()



if __name__ == '__main__':

	import sys
	from PySide2.QtWidgets import QApplication

	app = QApplication(sys.argv)
	win = LogWidget(handler=mainHandler)

	mainLogger.warning("test")
	testFn()

	win.show()
	sys.exit(app.exec_())
	pass


