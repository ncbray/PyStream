from util.python import uniqueSlotName
import collections

class Slots(object):
	def __init__(self):
		self.cache   = {}
		self.reverse = {}

	def uniqueSlotName(self, descriptor):
		if descriptor in self.cache:
			return self.cache[descriptor]

		uniqueName = uniqueSlotName(descriptor)

		self.cache[descriptor]   = uniqueName
		self.reverse[uniqueName] = descriptor

		return uniqueName

class CompilerContext(object):
	__slots__ = 'console', 'extractor', 'slots', 'stats'

	def __init__(self, console):
		self.console    = console
		self.extractor  = None
		self.slots      = Slots()
		self.stats      = collections.defaultdict(dict)
