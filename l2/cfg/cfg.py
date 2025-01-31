import json
import sys

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
      name = f'b{len(name2block)}'
    
    name2block.append((name, block))

  return name2block

def form_cfg(name2block): 
  cfg = []

  for i, (name, block) in enumerate(name2block):
    if not block:
      continue
    last = block[-1]

    if last['op'] in ('jmp', 'br'):
      succ = last['labels']
    elif last['op'] == 'ret' or i == len(name2block) - 1:
      succ = []
    else:
      succ = [name2block[i + 1][0]]

    cfg.append((name, succ))

  return cfg


def produce_dot(func_name, name2block, cfg):
    print(f"digraph {func_name} {{")
    for name, block in name2block:
        print(f" {name};".replace('.',''))
    for name, succs in cfg:
        for succ in succs:
            print(f" {name} -> {succ};".replace('.',''))
    print('}')

def main():
  prog = json.load(sys.stdin)
  for func in prog['functions']:

    name2block = block_map(form_blocks(func['instrs']))
    cfg = form_cfg(name2block)
    
    produce_dot(func['name'], name2block, cfg)

if __name__ == '__main__':
  main()