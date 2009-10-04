from .. import intrinsics

class IOTreeObj(object):
	def __init__(self, path):
		self.path     = path
		self.objMasks = {}
		self.fields   = {}

	def getField(self, field):
		if not field in self.fields:
			slot = IOTreeObj(self.path + (field,))
			self.fields[field] = slot
		else:
			slot = self.fields[field]
		return slot
				
def handleObj(dioa, obj, lut, mask, tobj):
	# Does this field actually exist?
	if mask is dioa.bool.false: return
	
	# Recurse into each of the object's fields
	fieldLUT = obj[0].slots
	index = obj[1]

	for name, field in fieldLUT.iteritems():
		# Don't ad intrinsic fields to the tree
		if intrinsics.isIntrinsicField(name): continue

		# Don't ad unused fields to the tree
		if field not in lut: continue
		
		# Handle the contents of the field.
		ctree = dioa.getValue(lut[field], index)
		handleCTree(dioa, ctree, lut, mask, tobj.getField(name))

def handleCTree(dioa, ctree, lut, mask, tobj):
	ctree = dioa.set.simplify(mask, ctree, dioa.set.empty)
	flat  = dioa.set.flatten(ctree)
	
	for obj in flat:
		# For each possible object, produce a correlated mask
		objleaf = dioa.set.leaf((obj,))
		omask = dioa.bool.in_(objleaf, ctree)
		omask = dioa.bool.and_(mask, omask)
		
		# Accumulate the mask
		oldmask = tobj.objMasks.get(obj, dioa.bool.false)
		tobj.objMasks[obj] = dioa.bool.or_(oldmask, omask)
		
		# Recurse
		handleObj(dioa, obj, lut, omask, tobj)

def printNode(tobj):
	print tobj.path
	print tobj.objMasks
	
	for field, next in tobj.fields.iteritems():
		printNode(next)

def evaluateLocal(dioa, lcl):
	if lcl is None: return None
		
	dataflow = dioa.dataflow
	lut = dataflow.entry.modifies
	node = lut[lcl]
	
	# The correlated tree
	ctree = dioa.getValue(node, 0)

	tobj = IOTreeObj((lcl,))

	handleCTree(dioa, ctree, lut, dioa.bool.true, tobj)
	
	if True:
		print
		print lcl
		printNode(tobj)
		print
	
	return tobj
