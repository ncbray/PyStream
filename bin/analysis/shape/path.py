# Set intersection
# Set intersection test
# Set union

# Path in set test
# Path kill
# Path point to kill
# Path union

##from PADS.UnionFind import UnionFind


class UnionFind(object):
	__slots__ = 'parents', 'weights'

	def __init__(self):
		self.parents = {}
		self.weights = {}

	def __getitem__(self, obj):
		if obj not in self.parents:
			return obj
		else:
			return self.getItemCompress(obj)

	def __iter__(self):
		return self.parents.iterkeys()

	def getItemCompress(self, obj):
		parent = self.parents[obj]
		if parent == obj:
			return parent
		else:
			root = self.getItemCompress(parent)
			self.parents[obj] = root
			return root

	def union(self, first, *objs):
		if objs:
			biggestRoot = self[first]
			maxWeight   = self.weights.get(biggestRoot, 1)
			roots       = set()
			roots.add(biggestRoot)

			for obj in objs:
				root   = self[obj]
				if root not in roots:
					weight = self.weights.get(root, 1)
					if weight > maxWeight:
						biggestRoot = root
						maxWeight   = weight
					roots.add(root)

			# The biggest root is intentionall left in roots,
			# So we ensure that self.parents[biggestRoot] exists.
			if len(roots) > 1:
				weight = 0
				for root in roots:
					self.parents[root] = biggestRoot
					weight += self.weights.pop(root, 1)

				self.weights[biggestRoot] = weight

			return biggestRoot
		else:
			return self[first]

	def copy(self):
		u = UnionFind()
		u.parents.update(self.parents)
		u.weights.update(self.weights)
		return u

	def dump(self):
		for k, v in self.parents.iteritems():
			print "%r  ->  %r" % (k, v)

##class PathEquivalence(object):
##	__slots__ = '_canonical', '_callback'
##	def __init__(self, callback):
##		self._canonical = {}
##		self._callback = callback
##
##	def checkInvariants(self):
##		for k, v in self._canonical.iteritems():
##			assert self._canonicalTail(k) == k, k
##			assert self.canonical(v) == v, v
##			assert len(k) >= len(v), (k, v)
##
##	def _canonicalCompress(self, path):
##		parent = self._canonical.get(path, path)
##
##		if path == parent:
##			return path
##		else:
##			root = self.canonical(parent)
##			self._canonical[path] = root
##			return root
##
##	def _canonicalTail(self, path):
##		tail, head = path.split()
##		
##		newtail = None if tail is None else self.canonical(tail)
##		if tail != newtail:
##			newpath = self._callback(newtail, head)
##		else:
##			newpath = path
##		return newpath
##	
##	def canonical(self, path):
##		newpath = self._canonicalTail(path)
##		compressed = self._canonicalCompress(newpath)
##		return compressed
##
##	def canonicalSet(self, paths):
##		if paths:
##			return set([self.canonical(path) for path in paths])
##		else:
##			return None
##
##	def union(self, *paths):
##		for path in paths:
##			assert not path.isNull()
##				
##		cpaths = [self.canonical(path) for path in paths]
##		cpathsSet = set(cpaths)
##		
##		if len(cpathsSet) > 1:
##			cfirst         = cpaths[0]
##			shortestPath   = cfirst
##			shortestLength = len(cfirst)
##
##			for cpath in cpathsSet:
##				l = len(cpath)
##				if  l < shortestLength:
##					shortestPath = cpath
##					shortestLength = l
##
##			#cpathsSet.remove(shortestPath) #?
##			for cpath in cpathsSet:
##				self._canonical[cpath] = shortestPath
##
##			self.compress()
##
##
##	def compress(self):
##		def chain(d, key, value):
##			if key != value:
##				# key -> value
##				
##				if key in d:
##					other = d[key]
##					if len(value) >= len(other):
##						# key -> other  and  value -> other
##						chain(d, value, other)
##					else:
##						# key -> value  and  other -> value
##						d[key] = value
##						chain(d, other, value)
##				else:			
##					d[key] = value
##
##		outp = {}		
##		for k, v in self._canonical.iteritems():
##			ck = self._canonicalTail(k)
##			cv = self.canonical(v)
##			chain(outp, ck, cv)
##
##		self._canonical = outp
##
##
##	def dump(self):
##		for k, v in self._canonical.iteritems():
##			print "%r  ->  %r" % (k, v)
##
##
##	def setIntersection(self, other):
##		pairC = {}
##
##		p = PathEquivalence() # Should error... untested?
##
##		def addValue(k):
##			c1 = self.canonical(k)
##			c2 = other.canonical(k)
##			pair = (c1, c2)
##			
##			if pair not in pairC:
##				pairC[pair] = k
##			else:
##				p.union(k, pairC[pair])
##
##		for k, v in self._canonical.iteritems():
##			addValue(k)
##			addValue(v)
##
##		p._canonical.update(outp)
##		return p
##
##	def setUnion(self, other):
##		p = PathEquivalence(self._callback)
##		p._canonical.update(self._canonical)
##
##		for k, v in other._canonical.iteritems():
##			p.union(k, v)
##		return p
##
##	def copy(self):
##		p = PathEquivalence(self._callback)
##		p._canonical.update(self._canonical)
##		return p
##
##	def filterUnstable(self, slot, stableValues):
##		p = PathEquivalence(self._callback)
##		rewrite = {}
##		
##		self.checkInvariants()
##
##		for k, v in self._canonical.iteritems():
##			# HACK None as first parameter
##			if k.stableValue(None, slot, stableValues):
##				if not v in rewrite:
##					if v.stableValue(None, slot, stableValues):
##						rewrite[v] = v
##					else:
##						rewrite[v] = k
##					
##			
##		assert False



class PathEquivalence(object):
	__slots__ = '_canonical', '_callback'
	def __init__(self, callback):
		self._canonical = UnionFind()
		self._callback  = callback

	
	def canonical(self, path):
		return self._canonical[path]

	def canonicalSet(self, paths):
		if paths:
			return set([self.canonical(path) for path in paths])
		else:
			return None

	def union(self, *paths):
		return self._canonical.union(*paths)

	def dump(self):
		for k, v in self._canonical.parents.iteritems():
			print "%r  ->  %r" % (k, v)


	def setIntersection(self, other):
		pairC = {}

		p = PathEquivalence() # Should error... untested?

		def addValue(k):
			c1 = self.canonical(k)
			c2 = other.canonical(k)
			pair = (c1, c2)
			
			if pair not in pairC:
				pairC[pair] = k
			else:
				p.union(k, pairC[pair])

		for k, v in self._canonical.iteritems():
			addValue(k)
			addValue(v)

		p._canonical.update(outp)
		return p

	def setUnion(self, other):
		p = self.copy()
		for k, v in other._canonical.parents.iteritems():
			p.union(k, v)
		return p

	def copy(self):
		p = PathEquivalence(self._callback)
		p._canonical = self._canonical.copy() # HACK?
		return p

	def filterUnstable(self, slot, stableValues):
		p = PathEquivalence(self._callback)
		rewrite = {}
		
		self.checkInvariants()

		for k, v in self._canonical.iteritems():
			# HACK None as first parameter
			if k.stableValue(None, slot, stableValues):
				if not v in rewrite:
					if v.stableValue(None, slot, stableValues):
						rewrite[v] = v
					else:
						rewrite[v] = k
					
			
		assert False
