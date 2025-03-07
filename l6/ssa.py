import json
import sys


def from_ssa(blocks):
    var2type = {}
    for block in blocks:
        for instr in block:
            if instr['op'] == 'get':
                var2type[instr['dest']] = instr['type']

    for block in blocks:
        curr_block = []
        for instr in block:
            # remove get
            if instr.get('op') == 'get':
                continue

            # set x y -> id y
            if instr.get('op') == 'set':
                new_isntr = {
                    'type': var2type[instr['args']],
                    'dest': shadow,
                    'op': 'id',
                    'args': var
                }


def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        pass
    
if __name__ == '__main__':
    main()