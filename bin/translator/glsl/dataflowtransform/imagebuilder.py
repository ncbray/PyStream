from language.python import ast
from analysis.dataflowIR import graph


leafTypes = (float, int, bool)

def isLeaf(ref):
	if ref.xtype.isExisting():
		# Naturaly unique
		return True

	# Constants don't need to be unique
	o = ref.xtype.obj
	return issubclass(o.type.pyobj, leafTypes)

def createIndex(analysis, ref):
	if isLeaf(ref):
		# The object is either a constant or a unique object.
		if analysis.getCount(ref) == 0:
			analysis.incrementCount(ref, unique=True)
		count = 0
	else:
		count = analysis.incrementCount(ref, unique=True)
	return count

class InputMemoryImageBuilder(object):
	def __init__(self, analysis):
		self.analysis = analysis
		self.pathRefs = {}
		self.process()

	def extendPath(self, path, slot):
		name = slot.slotName
		newPath = path + (name,)
		return newPath

	def inspectPath(self, path, refs):
		if not path in self.pathRefs: self.pathRefs[path] = set()

		entrySlots = self.analysis.dataflow.entry.modifies

		for ref in refs:
			if ref in self.pathRefs[path]: continue

			self.pathRefs[path].add(ref)
			for nextslot in ref:
				# If it's not defined, it's not used.
				if nextslot in entrySlots:
					self.inspectPath(self.extendPath(path, nextslot), nextslot)

	# Collects all possible objects for each unique path.
	# Relies on a lack of circular references in the memory image.
	# If recursive structures are ever allowed, we'll need to collapse SCCs.
	def findTypes(self):
		# Figure out the possible types for each unique path.
		for name, node in self.analysis.dataflow.entry.modifies.iteritems():
			if isinstance(node, graph.LocalNode):
				self.inspectPath((name.name,), name.annotation.references.merged)



	def buildPath(self, node, index, path, refs):
		assert isinstance(node, graph.SlotNode), node
		assert isinstance(index, int), index

		entrySlots = self.analysis.dataflow.entry.modifies

		for ref in refs:
			key = path, ref
			# Prevent redundant checking?
			# TODO remove this check when correlated?
			if key in self.analysis.pathObjIndex: continue


			count = createIndex(self.analysis, ref)
			self.analysis.pathObjIndex[key] = count

			old = self.analysis.getValue(node, index)
			leaf = self.analysis.set.leaf([(ref, count)])
			merged = self.analysis.set.union(old, leaf)
			self.analysis.setValue(node, index, merged)


			# Recurse
			for nextslot in ref:
				# If it's not defined, it's not used.
				if nextslot in entrySlots:
					nextnode = entrySlots[nextslot]
					self.buildPath(nextnode, count, self.extendPath(path, nextslot), nextslot)

	def buildImage(self):
		for name, node in self.analysis.dataflow.entry.modifies.iteritems():
			if isinstance(node, graph.LocalNode):
				self.buildPath(node, 0, (name.name,), name.annotation.references.merged)

	def process(self):
		self.findTypes()
		self.buildImage()


class AllocationMemoryImageBuilder(object):
	def __init__(self, analysis):
		self.analysis = analysis
		self.process()

	def process(self):
		for g in self.analysis.order:
			if isinstance(g, graph.GenericOp):
				op = g.op
				if isinstance(op, ast.TypeSwitch): continue

				assert op.annotation.allocates is not None, op
				allocates = op.annotation.allocates.merged
				for obj in allocates:
					self.analysis.allocateFreshIndex[obj] = createIndex(self.analysis, obj)
					#self.analysis.allocateMergeIndex[obj] = createIndex(self.analysis, obj)

def build(analysis):
	InputMemoryImageBuilder(analysis)
	AllocationMemoryImageBuilder(analysis)
