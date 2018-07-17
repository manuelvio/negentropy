# A python dictionary clone that supports multiple values with the same key.
# We delegate rather than subclass so any missing/new methods won't be inherited
# (with the wrong semantics).

import copy

class multidict_items(object):
	def __init__(self, md):
		self._md = md

	def __len__(self):
		return self._md._len

	def __iter__(self):
		for ki in self._md._dict.items():
			for vi in ki[1]:
				yield (ki[0], vi)

	def __contains__(self, item):
		return item in iter(self)

	def isdisjoint(self, other):
		for v in other:
			if v in self:
				return False
		return True

class multidict_keys(object):
	def __init__(self, md):
		self._md = md

	def __len__(self):
		return self._md._len

	def __iter__(self):
		for ki in self._md._dict.items():
			for i in range(0, len(ki)):
				yield ki[0]

	def __contains__(self, key):
		return key in self._md._dict

	def isdisjoint(self, other):
		for v in other:
			if v in self:
				return False
		return True

class multidict_values(object):
	def __init__(self, md):
		self._md = md

	def __len__(self):
		return self._md._len

	def __iter__(self):
		for ki in self._md._dict.items():
			for vi in ki[1]:
				yield vi

	def __contains__(self, value):
		return value in iter(self)

	def isdisjoint(self, other):
		for v in other:
			if v in self:
				return False
		return True

class multidict(object):
	def __init__(self, d=None):
		self._sel = 0
		if d is None:
			self._dict = {}
			self._len = 0
		elif isinstance(d, dict):
			# Allow initialisation from a regular dict 
			self._dict = d
			self._calclen()
		else:
			raise ValueError # TODO: match dict behaviour

	def clear(self):
		self._dict.clear()

	def copy(self):
		return copy.copy(self)

	@classmethod
	def fromkeys(cls, seq, value=None):
		md = cls()
		for v in seq:
			md[v] = value
		return md

	def get(self, key, default=None):
		items = self._dict.get(key)
		if items is None:
			return default
		else:
			return items[self._sel]

	def items(self):
		return multidict_items(self)

	def keys(self):
		return multidict_keys(self)

	def values(self):
		return multidict_values(self)

	def pop(self, key, default=None):
		ki = self._dict.get(key)
		if ki is not None:
			v = ki.pop(self._sel)
			if len(ki)==0:
				del self._dict[key]
			return v
		else:
			if default is None:
				raise KeyError(key)
			else:
				return default

	def popitem(self):
		# From the docs:
		#	Changed in version 3.7.
		#	LIFO order is now guaranteed. In prior versions, popitem() would
		#	return an arbitrary key/value pair.
		#
		# I can't justify the runtime or effort required to comply with this
		# behaviour. I'll implement the method but with semantics that don't
		# comply with >-3.7 behaviour.

		pass


#If key is in the dictionary, remove it and return its value,
#else return default. If default is not given and key is not
#in the dictionary, a KeyError is raised.

	def _calclen(self):
		self._len = 0
		for v in self._dict.values():
			self._len += len(v)

	def __len__(self):
		return self._len

	def __getitem__(self, key):
		try:
			items = self._dict[key]
		except KeyError:
			return self.__missing__(key)
		else:
			return items[self._sel]

	def __missing__(self, key):
		raise KeyError(key)

	def __setitem__(self, key, value):
		self._dict.setdefault(key, []).append(value)
		self._len += 1

	def __delitem__(self, key):
		#TODO: is this the behaviour we want?
		items = self._dict[key]
		if len(items)==1:
			del self._dict[key]
		else:
			del items[self._sel:]
		self._len -= 1

	def __iter__(self):
		return iter(self._dict)

	def __reversed__(self):
		raise TypeError("'multidict' object is not reversible")

	def __contains__(self, key):
		return key in self._dict

	def __repr__(self):
		return repr(self._dict)

	def __format__(self, format_spec):
		return self.dict.__format__(format_spec)

	def __eq__(self, other):
		return self._dict==other

	def __ne__(self, other):
		return self._dict!=other

if __name__=='__main__':
	a = {1: ["one", "One"], 2: ["two", "Two"], 3: ["three", "Three"]}
	m = multidict(a)
	
	print(m)
	print(m.pop(1))
	print(m)
	print(m.pop(1))
	print(m)

	print(m.pop(5, "Not there!"))
	print(m)
