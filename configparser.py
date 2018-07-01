from antlr4 import *
from antlrparser.configLexer import configLexer
from antlrparser.configParser import configParser
from antlrparser.configListener import configListener
import memmap
from interval import Interval
from inspect import cleandoc

def parse(ctx, fname):
	_Listener(ctx, fname)

def _getVariantValue(pe):
	def var2Type(v):
		if v.number():
			ns = v.number().getText()
			return int(ns[1:], 16) if ns[0]=='$' else int(ns)
		elif v.string_():
			return v.string_().getText()[1:-1]
		elif v.boolean_():
			return v.boolean_().getText()=='True'

	pval = pe.propval()
	v = pval.variant()
	if v:
		return var2Type(v)
	else:
		l = pval.list_()
		if l:
			return [var2Type(e) for e in l.variant()]

def _unpack_string(txt):
	if txt[:3]=="'''":
		return cleandoc(txt.strip("'''"))
	elif txt[:1]=="'":
		return txt.strip("'")
	elif txt[:1]=='"':
		return txt.strip('"')
	else:
		assert False, "Unexpected!"

def _propperties(node):
	props = {}
	props_node = node.properties()
	if props_node:
		for pe in props_node.propentry():
			name = pe.propname().getText()
			props[name] = _getVariantValue(pe)
	return props

class _Listener(configListener):
	def __init__(self, ctx, fname):
		if not fname:
			return
		self.ctx = ctx
		self.mem = map
		self.data_address = None

		input = FileStream(fname)
		lexer = configLexer(input)
		stream = CommonTokenStream(lexer)
		parser = configParser(stream)
		tree = parser.r()

		if parser.getNumberOfSyntaxErrors()==0:
			walker = ParseTreeWalker()
			walker.walk(self, tree)

	def enterDatasource(self, ctx:configParser.DatasourceContext):
		n = ctx.dsname()
		if n:
			n = name.getText()
		props = _propperties(ctx)
		self.ctx.parse_datasource(n, props)

	def enterMemmap(self, ctx:configParser.MemmapContext):
		self.ctx.memtype.parse_begin()

		body = ctx.mmbody()
		if body:
			for ent in body.mmentry():
				ft = ent.mmrange().mmfirst().getText()
				lt = ent.mmrange().mmlast().getText()
				dt = ent.mmdecoder().getText()
				dataaddr = ent.mmdataaddr()
				if not dataaddr is None:
					dataaddrt = dataaddr.getText()
					if dataaddrt=='*':
						self.data_address = None
					else:
						self.data_address = int(dataaddrt[1:], 16)

				props = _propperties(ent)

				self.ctx.memtype.parse_add(
						Interval(ft[1:], lt[1:]),
						self.ctx.decoders[dt],
						props,
						self.data_address
						)

				if not self.data_address is None:
					self.data_address += len(Interval(ft[1:], lt[1:]))

		self.ctx.memtype.parse_end(self.ctx)

	def enterAnnotate(self, ctx:configParser.AnnotateContext):
		self.ctx.syms.parse_begin(self.ctx)

	def enterLabel(self, ctx:configParser.LabelContext):
		addr = int(ctx.aaddress().getText()[1:], 16)
		name = ctx.lname().getText()
		in_index = 'i' in [f.getText() for f in ctx.lflags()]
		self.ctx.syms.parse_add(self.ctx, addr, name, in_index)

	def enterComment(self, ctx:configParser.CommentContext):
		# TODO: This is a mess. Make a comments class
		addr = int(ctx.aaddress().getText()[1:], 16)
		cmt = self.ctx.cmts[0].by_address.get(addr, ("", "", ""))
		txt = ctx.ctext().getText()
		pos = ctx.cpos()
		if pos is None:
			pos = '^'
		else:
			pos = pos.getText()
		if txt[:3]=="'''":
			if pos=='v':
				self.ctx.cmts[0].add((addr, cmt[1], _unpack_string(txt)))
			elif pos=='^':
				self.ctx.cmts[0].add((addr, _unpack_string(txt), cmt[2]))
			elif pos=='>':
				self.ctx.cmts[1].add((addr, _unpack_string(txt)))
		elif txt[:1]=="'":
			if pos=='v':
				self.ctx.cmts[0].add((addr, cmt[1], _unpack_string(txt)))
			elif pos=='^':
				self.ctx.cmts[0].add((addr, _unpack_string(txt), cmt[2]))
			elif pos=='>':
				self.ctx.cmts[1].add((addr, _unpack_string(txt)))
		elif txt[:1]=='"':
			if pos=='v':
				self.ctx.cmts[0].add((addr, cmt[1], _unpack_string(txt)))
			elif pos=='^':
				self.ctx.cmts[0].add((addr, _unpack_string(txt), cmt[2]))
			elif pos=='>':
				self.ctx.cmts[1].add((addr, _unpack_string(txt)))


	def exitAnnotate(self, ctx:configParser.AnnotateContext):
		self.ctx.syms.parse_end(self.ctx)