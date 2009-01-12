import util.compressedset

class PathInformation(object):
	__slots__ = 'hits', 'misses'

	def __init__(self, hits, misses):
		# Validate
		util.compressedset.validate(hits)
		util.compressedset.validate(misses)

		if hits:
			for hit in hits:
				assert hit.isExpression(), hit

		if misses:
			for miss in misses:
				assert miss.isExpression(), miss

		self.hits   = hits if hits else None
		self.misses = misses if misses else None

	def classifyHitMiss(self, e):
		isHit  = e in self.hits if self.hits else False
		isMiss = e in self.misses if self.misses else False
		return isHit, isMiss
	
	def inplaceMerge(self, other):
		hits, hitsChanged = util.compressedset.inplaceIntersection(self.hits, other.hits)
		if hitsChanged: self.hits = hits

		misses, missesChanged = util.compressedset.inplaceIntersection(self.misses, other.misses)
		if missesChanged: self.misses = misses

		return self, (hitsChanged or missesChanged)

	def copy(self):
		hits   = util.compressedset.copy(self.hits)
		misses = util.compressedset.copy(self.misses)
		return PathInformation(hits, misses)

	def unionHitMiss(self, additionalHits, additionalMisses):
		# HACK?
		newHits   = util.compressedset.union(self.hits,   additionalHits)
		newMisses = util.compressedset.union(self.misses, additionalMisses)
		return PathInformation(newHits, newMisses)

		
	def filterUnstable(self, sys, slot, stableValues):
		def filterUnstable(sys, exprs, slot, stableValues):
			if exprs:
				if exprs is stableValues:
					# Optimization, all the values are known stable, so just check the locations.
					return util.compressedset.copy([e for e in exprs if e.stableLocation(sys, slot, stableValues)])
				else:	
					return util.compressedset.copy([e for e in exprs if e.stableValue(sys, slot, stableValues)])
			else:
				return util.compressedset.nullSet
			
		newHits   = filterUnstable(sys, self.hits,   slot, stableValues)
		newMisses = filterUnstable(sys, self.misses, slot, stableValues)
		return PathInformation(newHits, newMisses)

	def unify(self, sys, e1, e0):
		def substituteUpdate(sys, expressions, e1, e0):
			if expressions:
				newExpressions = set()
				for e in expressions:
					newE = e.substitute(sys, e1, e0)

					# Local references are "trivial" as they can be easily infered from the configuration.
					if newE and not newE.isTrivial():
						newExpressions.add(newE)
				expressions.update(newExpressions)
		
		substituteUpdate(sys, self.hits,   e1, e0)
		substituteUpdate(sys, self.misses, e1, e0)
