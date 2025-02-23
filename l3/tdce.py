
import json
import sys

from blocks import form_blocks

def tdce(instrs):
    changed = True

    while changed:
        changed = False
        used = set()
        for instr in instrs:
            if 'args' in instr:
                for arg in instr['args']:
                    used.add(arg)

        new_instrs = []
        for instr in instrs:
            if 'dest' in instr and instr['dest'] not in used:
                changed = True
            else:
                new_instrs.append(instr)
        instrs = new_instrs

    return instrs

def remove_dead_stores(block):
    changed = True
    while changed:
        changed = False
        assigned_but_unused = {}
        remove = set()

        for i, instr in enumerate(block):

            # check for uses
            if 'args' in instr:
                for arg in instr['args']:
                    if arg in assigned_but_unused:
                        assigned_but_unused.pop(arg)

            # check for defs
            if 'dest' in instr:
                if instr['dest'] in assigned_but_unused:
                    remove.add(assigned_but_unused[instr['dest']])
                    changed = True
                assigned_but_unused[instr['dest']] = i

        new_instrs = []
        for i, instr in enumerate(block):
            if i not in remove:
                new_instrs.append(instr)
        block = new_instrs
            
    return new_instrs
        

def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:
        func['instrs'] = tdce(func['instrs'])

        blocks = form_blocks(func['instrs'])

        new_blocks = []
        for block in blocks:
            new_blocks.append(remove_dead_stores(block))

        func['instrs'] = [instr for block in new_blocks for instr in block]

    json.dump(prog, sys.stdout, indent=2)

if __name__ == '__main__':
    main()