import jinja2
import webbrowser
import decoders
from interval import Interval
import gfx
import data
import M6502
import index

def render(env, template_name, **template_vars):
	template = env.get_template(template_name)
	return template.render(**template_vars)

def sequence_to_string(it, pat, **kwargs):
	sep = kwargs.get("s")
	if sep is None or isinstance(sep, str):
		if sep is None:
			sep = " "
		ret = sep.join([pat.format(i) for i in it])
	else:
		ret = ""
		sep.sort(reverse=True)
		for i in enumerate(it):
			if i[0]!=0:
				for s in sep:
					if i[0]%s[0]==0:
						ret = ret+s[1]
						break
			ret = ret+pat.format(i[1])

	pad = kwargs.get("w")
	if pad:
		ret = ret.ljust(pad)

	return ret

def run(args):
	bd = decoders.Context(
				decoders = {
					"bitmap" : gfx.CharDecoder("chars"),
					"data" : data.BytesDecoder("data", 16),
					"ptr16" : data.PointerDecoder("ptr16", 4),
					"code" : M6502.M6502Decoder("code")
					},
				default_decoder = args.defaultdecoder,
				address = 0x5000,
				memory = args.input,
				memtype = args.memtype,
				symbols = ("BD.txt", "BD-BM.txt"),
				comments = "Comments.txt"
		)


	env = jinja2.Environment(loader=jinja2.PackageLoader(__name__))
	env.globals['title'] ="Boulder Dash Disassembly"
	env.globals['items'] = bd.items()
	env.globals['index'] = index.get_index(bd.syms)
	env.filters['seq2str'] = sequence_to_string

	s = render(env, 'template.html')
	with open(args.output, "w") as of:
		of.write(s)

	if args.webbrowser:
		webbrowser.open(args.output)
