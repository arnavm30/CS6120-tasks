from collections import defaultdict

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

def block_map(blocks):
    name2block = []

    for block in blocks: 
        if block and 'label' in block[0]:
            name = block[0]['label']
            block = block[1:]
        else:
            name = f'b{len(name2block) + 1}'
    
        name2block.append((name, block))

    return name2block

def form_cfg(name2block): 
    cfg = defaultdict(lambda: {'preds': [], 'succs': []})
    
    for i, (name, block) in enumerate(name2block):
        if not block:
            continue

        last = block[-1]
        if last['op'] in ('jmp', 'br') and 'labels' in last:
            for label in last['labels']:
                cfg[name]['succs'].append(label)
                cfg[label]['preds'].append(name)

        elif last['op'] != 'ret' and i != len(name2block) - 1:
            next_name = name2block[i + 1][0]
            cfg[name]['succs'].append(next_name)
            cfg[next_name]['preds'].append(name)
    
    return cfg
