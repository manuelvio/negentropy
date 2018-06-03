from enum import Enum, unique, auto
from heapq import merge
import memory as memmod
import memmap
import symbols as symmod
from interval import Interval

@unique
class CuttingPolicy(Enum):
	Automatic = auto()
	Guided  = auto()
	Dont = auto()

class GuidedCutter(object):
	def __init__(self, ctx, ivl, coll):
		self.cuts = merge(ctx.syms.keys_in_range(ivl), ctx.cmts.keys_in_range(ivl))
		self.current = Interval()
		self.coll = coll
		self._next_cut()

	def _next_cut(self):
		try:
			self.cut = next(self.cuts)
		except StopIteration:
			self.cut = None

	# Add an atomic region that can't be cut. Cuts only occur at joins.
	# If a cut point isn't present at a join the regions are merged.
	# Cuts at other locations are ignored.
	# TODO: flag the ignored cuts and log.
	def atomic(self, ivl):
		self.current = Interval.union(self.current, ivl)
		if self.cut is None:
			return

		while self.cut<=ivl.last:
			self._next_cut()
			if self.cut is None:
				return

		if self.cut==(ivl.last+1):
			self.coll.append(self.current)
			self.current = Interval()

	def done(self):
		if not self.current.is_empty():
			self.coll.append(self.current)

class Context(object):
	def __init__(self, decoders, address, memory, 
				memtype, default_decoder, symbols,
				comments, flags, authoring_info):
		self.decoders = decoders
		with open(memory, "rb") as f:
			contents = f.read()
			self.mem = memmod.Memory(contents, address)
		self.mem_range = self.mem.range()
		self.syms = symmod.read_symbols(symbols)
		self.cmts = symmod.read_comments(comments)
		self.links_referenced_addresses = set()
		self.links_reachable_addresses = set()
		self.holes = 0
		self.memtype = memmap.MemType(self, memtype, default_decoder)
		self.flags = flags
		self.authoring_info = authoring_info

	def link_add_referenced(self, addr):
		self.links_referenced_addresses.add(addr)

	def link_add_reachable(self, addr):
		self.links_reachable_addresses.add(addr)

	def is_destination(self, addr):
		 return (addr in self.links_reachable_addresses and 
		 		 addr in self.links_referenced_addresses)

	def preprocess(self, ivl=None):
		if not ivl:
			ivl = self.mem_range
		self.memtype.preprocess(self, ivl)

	def items(self, ivl=None):
		if not ivl:
			ivl = self.mem_range
		return self.memtype.items(self, ivl)

class Prefix(object):
	def prefix(self, ctx, ivl, params):
		c = ctx.cmts.by_address.get(ivl.first)
		is_destination = ctx.is_destination(ivl.first)
		params['target_already_exits'] = is_destination
		s = ctx.syms.by_address.get(ivl.first)
		if ctx.authoring_info:
			info = {'authoring_info': 
					{'ivl': ivl,
					 'type': self.name
					}
				   }
		else:
			info = {}
		return {
			'type': "prefix",
			'address': ivl.first,
			**info,
			'is_destination' : is_destination,
			'label': None if s is None else s[1],
			'comment_before': None if c is None else c[1],
			'comment_after': None if c is None else c[2],
			'comment_inline': None if c is None else c[3]
			}

	def cutting_policy(self):
		return CuttingPolicy.Automatic
