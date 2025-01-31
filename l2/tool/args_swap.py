import json
import sys

ADDS_MULS = 'add, mul, fadd, fmul'
CMP = 'gt, lt, ge, le'

def adds_muls_swaps(instrs):
  for instr in instrs:
    if 'op' in instr and instr['op'] in ADDS_MULS:
      instr['args'].reverse()

def swap_bool_cmp(instrs):
  for instr in instrs:
    if 'op' in instr and instr['op'] in CMP:
      if instr['op'] == 'gt':
        instr['op'] = 'le'
        instr['args'].reverse()
      elif instr['op'] == 'lt':
        instr['op'] = 'ge'
        instr['args'].reverse()
      elif instr['op'] == 'ge':
        instr['op'] = 'lt'
        instr['args'].reverse()
      else:
        instr['op'] = 'gt'
        instr['args'].reverse()

def swap_branches(instrs):
  new_instrs = []

  for instr in instrs:
    if 'op' in instr and instr['op'] == 'br':
      cond_var = instr['args'][0]
      btarg_true = instr['labels'][0]
      btarg_false = instr['labels'][1]

      # Find definition of cond
      cond_def = None
      for prev_instr in instrs:
        if 'dest' in prev_instr and prev_instr['dest'] == cond_var:
          cond_def = prev_instr
          break

      if cond_def and cond_def['op'] == 'const' and cond_def['type'] == 'bool':
        # Flip cond value and branch targets
        flipped_value = not cond_def['value']

        new_instrs.append({
          'op': 'const',
          'type': 'bool',
          'dest': cond_var,
          'value': flipped_value
        })

        new_instrs.append({
          'op': 'br',
          'args': [cond_var],
          'labels': [btarg_false, btarg_true]
        })
      else:
        # Keep original branch if condition is not a constant
        new_instrs.append(instr)
    else:
      new_instrs.append(instr)

  return new_instrs

def main():
  prog = json.load(sys.stdin)
  for func in prog['functions']:
    adds_muls_swaps(func['instrs'])
    # swap_bool_cmp(func['instrs'])
    # func['instrs'] = swap_branches(func['instrs'])

  print(json.dumps(prog, indent=2))
  
if __name__ == '__main__':
  main()