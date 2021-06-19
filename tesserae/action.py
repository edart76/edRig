
""" Class representing combination of partial function and event -
a 'partial-plus' if you will """

from __future__ import annotations

from typing import List, Set, Dict, Callable
from functools import partial

def evalLambdaSequence(seq):
	"""if any entries in sequence are lambdas, evaluate them"""

class Action(object):
	""" Named partial, also able to be combined with others
	"""
	def __init__(self,
	             fn:callable=None,
	             name="",
	             args=(),
	             kwargs:Dict=None,
	             evalLambdas=True):
		""":param evalLambdas: if lambdas are given as part
		of args or kwargs, they will be evaluated
		when action executes"""
		self.fn = fn
		self._name = name
		self.args = args
		self.kwargs = kwargs or {}
		self.subActions = [] # no need for full tree here

	@property
	def name(self):
		if self._name: return self._name
		if isinstance(self.fn, partial):
			return self.fn.func.__name__
		return self.fn.__name__

	def addAction(self, action):
		if not isinstance(action, Action):
			action = Action(action)
		self.subActions.append(action)

	def execute(self):
		"""calls the actions function with given parametres"""
		if isinstance(self.fn, partial):
			return self.fn()
		result = self.fn(*self.args, **self.kwargs)
		for i in self.subActions:
			i.execute()
		return result
