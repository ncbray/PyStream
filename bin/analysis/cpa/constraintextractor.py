from util.typedispatch import *

from programIR.python import ast
from programIR.python import program

from common import opnames
from stubs.stubcollector import exports


from constraints import *



class ExtractDataflow(object):
	__metaclass__ = typedispatcher

	def __init__(self, system, code, context):
		self.system  = system
		self.code    = code
		self.context = context

		self.processed = set()

	def doOnce(self, node):
		return True

		if not node in self.processed:
			self.processed.add(node)
			return True
		else:
			return False

	def contextual(self, lcl):
		if lcl is not None:
			return self.system.canonical.local(self.code, lcl, self.context)
		else:
			return None

	def contextOp(self, node):
		return self.system.canonical.opContext(self.code, node, self.context)

	def opPath(self, node):
		return self.context.signature.path.advance(node)

	def directCall(self, node, code, selfarg, args, vargs, kargs, target):
		if self.doOnce(node):
			assert isinstance(code, ast.Code), type(code)
			op   = self.contextOp(node)
			path = self.opPath(node)
			kwds = [] # HACK
			con = DirectCallConstraint(op, path, code, selfarg, args, kwds, vargs, kargs, target)
			con.attach(self.system) # TODO move inside constructor?
		return target

	def assign(self, src, dst):
		self.system.createAssign(src, dst)

	def init(self, node, obj):
		result = self.contextual(node)
		if self.doOnce(node):
			self.system.update(result, (self.system.existingObject(obj),))
		return result

	def call(self, node, expr, args, kwds, vargs, kargs, target):
		if self.doOnce(node):
			op   = self.contextOp(node)
			path = self.opPath(node)
			con = CallConstraint(op, path, expr, args, kwds, vargs, kargs, target)
			con.attach(self.system) # TODO move inside constructor?
		return target

	def load(self, node, expr, fieldtype, name, target):
		if self.doOnce(node):
			op   = self.contextOp(node)
			con = LoadConstraint(op, expr, fieldtype, name, target)
			con.attach(self.system) # TODO move inside constructor?
		return target

	def store(self, node, expr, fieldtype, name, value):
		op   = self.contextOp(node)
		con = StoreConstraint(op, expr, fieldtype, name, value)
		con.attach(self.system) # TODO move inside constructor?

	def allocate(self, node, expr, target):
		if self.doOnce(node):
			op   = self.contextOp(node)
			path = self.opPath(node)
			con = AllocateConstraint(op, path, expr, target)
			con.attach(self.system) # TODO move inside constructor?
		return target


	##################################
	### Generic feature extraction ###
	##################################

	@defaultdispatch
	def default(self, node):
		assert False, repr(node)

	@dispatch(str, type(None))
	def visitJunk(self, node):
		pass

	@dispatch(ast.Suite, ast.Condition)
	def visitOK(self, node):
		for child in ast.children(node):
			self(child)


	@dispatch(list)
	def visitList(self, node):
		return [self(child) for child in node]

	@dispatch(tuple)
	def visitTuple(self, node):
		return tuple([self(child) for child in node])

	@dispatch(ast.ConvertToBool)
	def visitConvertToBool(self, node, target):
		return self.directCall(node, exports['convertToBool'].code,
			None, [self(node.expr)],
			None, None, target)

	@dispatch(ast.BinaryOp)
	def visitBinaryOp(self, node, target):
		if node.op in opnames.inplaceOps:
			opname = opnames.inplace[node.op[:-1]]
		else:
			opname = opnames.forward[node.op]

		return self.directCall(node, exports['interpreter%s' % opname].code,
			None, [self(node.left), self(node.right)],
			None, None, target)

	@dispatch(ast.UnaryPrefixOp)
	def visitUnaryPrefixOp(self, node, target):
		opname = opnames.unaryPrefixLUT[node.op]
		return self.directCall(node, exports['interpreter%s' % opname].code,
			None, [self(node.expr)],
			None, None, target)

	@dispatch(ast.GetGlobal)
	def visitGetGlobal(self, node, target):
		return self.directCall(node, exports['interpreterLoadGlobal'].code,
			None, [self(self.code.selfparam), self(node.name)],
			None, None, target)

	@dispatch(ast.GetIter)
	def visitGetIter(self, node, target):
		return self.directCall(node, exports['interpreter_iter'].code,
			None, [self(node.expr)],
			None, None, target)

	@dispatch(ast.Call)
	def visitCall(self, node, target):
		return self.call(node, self(node.expr),
			self(node.args), self(node.kwds),
			self(node.vargs), self(node.kargs), target)

	@dispatch(ast.DirectCall)
	def visitDirectCall(self, node, target):
		return self.directCall(node, node.func,
			self(node.selfarg), self(node.args),
			self(node.vargs), self(node.kargs), target)

	@dispatch(ast.BuildList)
	def visitBuildList(self, node, target):
		return self.directCall(node, exports['buildList'].code,
			None, self(node.args),
			None, None, target)

	@dispatch(ast.BuildTuple)
	def visitBuildTuple(self, node, target):
		return self.directCall(node, exports['buildTuple'].code,
			None, self(node.args),
			None, None, target)

	@dispatch(ast.UnpackSequence)
	def visitUnpackSequence(self, node):
		# HACK oh so ugly... does not resemble what actually happens.
		for i, arg in enumerate(node.targets):
			obj = self.system.extractor.getObject(i)
			target = self.contextual(arg)
			self.directCall(node, exports['interpreter_getitem'].code,
				None, [self(node.expr), self(ast.Existing(obj))],
				None, None, target)

	@dispatch(ast.GetAttr)
	def visitGetAttr(self, node, target):
		return self.directCall(node, exports['interpreter_getattribute'].code,
			None, [self(node.expr), self(node.name)],
			None, None, target)

	@dispatch(ast.SetAttr)
	def visitSetAttr(self, node):
		return self.directCall(node, exports['interpreter_setattr'].code,
			None, [self(node.expr), self(node.name), self(node.value)],
			None, None, None)

	@dispatch(ast.Assign)
	def visitAssign(self, node):
		self(node.expr, self(node.lcl))

	@dispatch(ast.Discard)
	def visitDiscard(self, node):
		self(node.expr, None)

	@dispatch(ast.Return)
	def visitReturn(self, node):
		self.assign(self(node.expr), self(self.code.returnparam))

	@dispatch(ast.Local)
	def visitLocal(self, node):
		return self.contextual(node)

	@dispatch(ast.Existing)
	def visitExisting(self, node):
		# TODO refine?
		return self.init(node.object, node.object)

	@dispatch(ast.Load)
	def visitLoad(self, node, target):
		return self.load(node, self(node.expr), node.fieldtype, self(node.name), target)

	@dispatch(ast.Store)
	def visitStore(self, node):
		return self.store(node, self(node.expr), node.fieldtype, self(node.name), self(node.value))

	@dispatch(ast.Allocate)
	def visitAllocate(self, node, target):
		return self.allocate(node, self(node.expr), target)

	@dispatch(ast.Switch)
	def visitSwitch(self, node):
		self(node.condition)

		cond = self.contextual(node.condition.conditional)
		con = DeferedSwitchConstraint(self, cond, node.t, node.f)
		con.attach(self.system) # TODO move inside constructor?

	@dispatch(ast.For)
	def visitFor(self, node):
		self(node.loopPreamble)

		self(node.bodyPreamble)
		self(node.body)

		if node.else_:
			self(node.else_)

	@dispatch(ast.Code)
	def visitCode(self, node):
		self(node.ast)


