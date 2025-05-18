TERMINATORS = 'br', 'jmp', 'ret'

def form_blocks(instrs):
    blocks = []
    cur_block = []
    for instr in instrs:
        if 'op' in instr:
            cur_block.append(instr)

            if instr['op'] in TERMINATORS:
                blocks.append(cur_block)
                cur_block = []

        else:
            if cur_block:
                blocks.append(cur_block)
            cur_block = [instr]

    if cur_block:
        blocks.append(cur_block)

    return blocks