from . import decoders
from .M6502 import *
from . import symbols

class M6502Decoder(decoders.Prefix):
    def __init__(self, name):
        self.name = name

    def cutting_policy(self):
        return decoders.CuttingPolicy.Guided

    def preprocess(self, ctx, ivl, cutter):
        ii = None
        for ii in M6502Iterator(ctx.mem, ivl):
            cutter.atomic(ii.ivl)
            ctx.link_add_reachable(ii.ivl.first)
            if ii.target is not None:
                ctx.link_add_referenced(ii.target)
        cutter.done()
        # return the non-processed part of the interval
        return ivl if ii is None else Interval(ii.ivl.last+1, ivl.last)

    def decode(self, ctx, ivl, params):
        def lines(self):
            ctx.directives.reset(ivl.first)
            target_already_exits = params['target_already_exits']

            hide_a = ctx.options.get("hide_a", False)
            pc_rel = ctx.options.get("pc_rel", False)
            for ii in M6502Iterator(ctx.mem, ivl, hide_a):
                def format_numerical_operand(v):
                    if ii.mode_info.operand_size==0:
                        return ""
                    elif ii.op_info.mode==AddrMode.Relative or ii.mode_info.operand_size==2:
                        return "${:04x}".format(v)
                    elif ii.mode_info.operand_size==1:
                        return "${:02x}".format(v)

                oper = symbols.Operand(ctx)
                d = ctx.directives.lookup(ii.ivl.first)

                if ii.target:
                    if d:
                        oper = d.operand(ctx, ii.target)
                    else:
                        e = ctx.syms.lookup(ii.target, name_unknowns=False)
                        optext = e.name
                        if optext is None:
                            if pc_rel and ii.op_info.flow_transfer:
                                optext = "*"+symbols.format_op_adjust(e.addr-ii.ivl.first)
                            else:
                                optext = format_numerical_operand(e.addr)
                        oper.post(optext, e.addr)
                        if e.op_adjust:
                            oper.post(e.op_adjust_str())
                else:
                    if d is None:
                        oper.post(format_numerical_operand(ii.operand))
                    else:
                        oper = d.operand(ctx, ii.operand)

                c = ctx.cmts.get_inline(ii.ivl.first)

                yield {
                    'address': ii.ivl.first,
                    'is_destination' : (not target_already_exits) and ctx.is_destination(ii.ivl.first),
                    'bytes': ctx.mem.r8m(ii.ivl.first, ii.mode_info.operand_size+1),
                    'comment': None if c is None else c[1],
                    'instruction': {
                        'mnemonic': ii.op_info.mnemonic,
                        'pre': ii.mode_info.pre,
                        'post': ii.mode_info.post,
                        'operand': oper,
                        }
                    }

                target_already_exits = False

        return {
                'type': self.name,
                'lines': lines(self)
                }
