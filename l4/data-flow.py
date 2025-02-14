import json
import sys

from cfg import *

EMPTY_SET = '∅'

class DataFlowAnalysis:
    def __init__(self, args, init, merge, transfer, direction='forward'):
        self.args = args
        self.init = init
        self.merge = merge
        self.transfer = transfer
        self.direction = direction

    def merge(self, preds): 
        return self.merge(preds)
        
    def transfer(self, in_b, name2block):
        return self.transfer(in_b, name2block)

    def data_flow(self, name2block):
        in_ = {name: self.init for name, _ in name2block}
        out = {name: self.init for name, _ in name2block}

        cfg = form_cfg(name2block)

        worklist = [(name, block) for (name, block) in name2block]

        if self.direction == 'forward':
            in_[worklist[0][0]] = set().union(*self.args)
        else:
            for name in cfg:
                cfg[name]['preds'], cfg[name]['succs'] = cfg[name]['succs'], cfg[name]['preds']
            worklist = list(reversed(worklist))

        while worklist:
            b = worklist.pop(0)

            inputs = [out[pred] for pred in cfg[b[0]]['preds']]

            in_[b[0]] = in_[b[0]].union(self.merge(inputs))
            out_b = self.transfer(in_[b[0]], b)

            if out[b[0]] != out_b:
                out[b[0]] = out_b
                for succ in cfg[b[0]]['succs']:
                    for name, block in name2block:
                        if name == succ:
                            worklist.append((succ, block))
                            break
        
        if self.direction == 'backward':
            in_, out = out, in_
        return in_, out

class ReachingDefinitions(DataFlowAnalysis):
    def __init__(self, args):
        def merge(preds):
            return set().union(*preds)

        def transfer(in_b, name2block):
            name, block = name2block
            defs = set()
            kill = set()
            for i, instr in enumerate(block):
                if 'dest' in instr:
                    for def_ in in_b:
                        if instr['dest'] == def_[0]:
                            kill.add(def_)

                    defs.add((instr['dest'], name, i))
            
            return defs.union(in_b - kill)

        super().__init__(args, set(), merge, transfer)

class LiveVariables(DataFlowAnalysis):
    def __init__(self, args):
        def merge(preds):
            return set().union(*preds)

        def transfer(in_b, name2block):
            _, block = name2block
            written = set()
            read = set()
            for instr in block:
                if 'args' in instr:
                    for arg in instr['args']:
                        read.add(arg) if arg not in written else ()
                if 'dest' in instr:
                    written.add(instr['dest'])

            return read.union(in_b - written)

        super().__init__(args, set(), merge, transfer, direction='backward')

def run(analysis, name2block):
    in_, out = analysis.data_flow(name2block)

    for name, _ in name2block:
        print(f'{name}:')
        print(f'  in:  {', '.join(map(str, sorted(in_[name]))) if in_[name] else EMPTY_SET}')
        print(f'  out: {', '.join(map(str, sorted(out[name]))) if out[name] else EMPTY_SET}')

if __name__== "__main__":
    prog = json.load(sys.stdin)
    for func in prog["functions"]:
        blocks = form_blocks(func['instrs'])
        name2block = block_map(blocks)
        
        match str(sys.argv[1]):
            case 'live':
                args = [((arg['name']) for arg in func['args'])] if 'args' in func else []
                run(LiveVariables(args), name2block)
            case 'reaching':
                args = [((arg['name'], None, None) for arg in func['args'])] if 'args' in func else []
                run(ReachingDefinitions(args), name2block)
            case _:
                print('Invalid analysis')
