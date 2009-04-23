from language.python import ast
from language.python import program
from language.python import annotations

def isZero(arg):
	return isinstance(arg, ast.Existing) and arg.object.isConstant() and arg.object.pyobj == 0

def isOne(arg):
	return isinstance(arg, ast.Existing) and arg.object.isConstant() and arg.object.pyobj == 1

def isNegativeOne(arg):
	return isinstance(arg, ast.Existing) and arg.object.isConstant() and arg.object.pyobj == -1

def hasNumArgs(node, count):
	return len(node.args) == count and not node.kwds and not node.vargs and not node.kargs

def isAnalysisInstance(node, type):
	if isinstance(node, ast.Existing) and node.object.isConstant():
		return isinstance(node.object.pyobj, type)
	elif isinstance(node, ast.Local):
		if not node.annotation.references[0]:
			return False

		for ref in node.annotation.references[0]:
			obj = ref.xtype.obj
			if obj.isConstant():
				if not isinstance(obj.pyobj, type):
					return False
			else:
				if not hasattr(obj, 'type'):
					return False

				if not issubclass(obj.type.pyobj, type):
					return False
		return True

	return False

def isAnalysis(arg, tests):
	return isinstance(arg, ast.Existing) and isinstance(arg.object, program.Object) and arg.object.pyobj in tests

class DirectCallRewriter(object):
	def __init__(self, extractor):
		self.extractor = extractor
		self.exports = extractor.stubs.exports
		self.rewrites = {}

	def addRewrite(self, name, func):
		code = self.exports.get(name)
		self._bindCode(code, func)

	def attribute(self, type, name, func):
		attr = type.__dict__[name]
		origin = annotations.functionOrigin(attr)
		self._bindOrigin(origin, func)

	def function(self, obj, func):
		origin = annotations.functionOrigin(obj)
		self._bindOrigin(origin, func)

	def _bindCode(self, code, func):
		if code:
			origin = code.annotation.origin
			self._bindOrigin(origin, func)

	def _bindOrigin(self, origin, func):
		if origin not in self.rewrites:
			self.rewrites[origin] = [func]
		else:
			self.rewrites[origin].append(func)

	def __call__(self, node):
		origin = node.func.annotation.origin
		if origin in self.rewrites:
			for rewrite in self.rewrites[origin]:
				result = rewrite(node)
				if result is not None:
					return result
		return None