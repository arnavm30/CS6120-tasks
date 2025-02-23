import json
import sys

from blocks import form_blocks 

COMMUTATIVE_OPS = ['add', 'mul', 'fadd', 'fmul', 'eq', 'and', 'or']
FOLDABLE_OPS = {
    'add': lambda a, b: a + b,
    'sub': lambda a, b: a - b,
    'mul': lambda a, b: a * b,
    'div': lambda a, b: a // b if b != 0 else None,
    'eq': lambda a, b: a == b,
    'lt': lambda a, b: a < b,
    'gt': lambda a, b: a > b,
    'le': lambda a, b: a <= b,
    'ge': lambda a, b: a >= b,
    'and': lambda a, b: a and b,
    'or': lambda a, b: a or b,
}

def lvn_block(block):
    table = {}
    var2num = {}
    counter = 0
    
    def fresh_num():
        nonlocal counter
        counter += 1
        return counter
    
    def add_to_table(var, val_tuple):
        num = fresh_num()
        var2num[var] = num
        table[num] = (val_tuple, var)
        return num
    
    def is_const(var):
        val_tuple, _ = table[var2num[var]]
        return isinstance(val_tuple, tuple) and val_tuple[0] == 'const'
    
    def get_const_value(var):
        val_tuple, _ = table[var2num[var]]
        return val_tuple[1]
    
    def find_existing_value(val_tuple):
        for num, (val, var) in table.items():
            if val == val_tuple and var is not None:
                return True, num, var
        return False, None, None
    
    def create_id_instruction(src_var, dest, instr_type):
        result = {
            'op': 'id',
            'args': [src_var],
            'dest': dest
        }
        if instr_type:
            result['type'] = instr_type
        return result
    
    def fold_constants(op, args):
        if op == 'not':
            return not args[0]
            
        a, b = args
        if op in FOLDABLE_OPS:
            return FOLDABLE_OPS[op](a, b)
        
    # identify variables that are written multiple times
    overwritten = set()
    seen_vars = set()
    for instr in block:
        if 'dest' in instr:
            dest = instr['dest']
            if dest in seen_vars:
                overwritten.add(dest)
            seen_vars.add(dest)
    
    # main LVN alg
    new_instrs = []
    
    for instr in block:
        if 'op' not in instr:
            new_instrs.append(instr)
            continue
        
        new_instr = instr.copy()
        
        if 'args' in instr:
            for arg in instr['args']:
                if arg not in var2num:
                    add_to_table(arg, ('val', arg))
        
        if 'dest' not in instr:
            new_instrs.append(new_instr)
            continue
        
        dest = instr['dest']

        if instr['op'] == 'const':
            value_type = instr.get('type', 'int')
            val_tuple = ('const', instr['value'], value_type)
            
            found, num, var = find_existing_value(val_tuple)
            if found:
                var2num[dest] = num
                new_instr = create_id_instruction(var, dest, instr.get('type', None))
            else:
                add_to_table(dest, val_tuple)
        
        elif instr['op'] == 'id':
            src = instr['args'][0]
            
            if dest in overwritten:
                add_to_table(dest, ('id', var2num[src]))
            else:
                # follow the copy chain to its source
                src_num = var2num[src]
                val, canonical_var = table[src_num]
                
                while (isinstance(val, tuple) and val[0] == 'id' and 
                       table[val[1]][1] is not None):
                    
                    next_num = val[1]
                    next_val, next_var = table[next_num]
                    
                    if next_var in overwritten or any(
                        i.get('op') == 'call' and 'dest' in i and i['dest'] == next_var 
                        for i in block
                    ):
                        break
                    
                    src_num = next_num
                    val, canonical_var = next_val, next_var
                
                var2num[dest] = src_num
                
                if canonical_var is None:
                    table[src_num] = (val, dest)
        
        elif 'args' in instr and instr['args']:
            value_type = instr.get('type', 'int')
                        
            if (instr['op'] in FOLDABLE_OPS and all(is_const(arg) for arg in instr['args'])):
                const_args = [get_const_value(arg) for arg in instr['args']]
                folded_val = fold_constants(instr['op'], const_args)
                
                if folded_val is not None:
                    new_instr = {
                        'op': 'const',
                        'dest': dest,
                        'value': folded_val
                    }
                    if 'type' in instr:
                        new_instr['type'] = instr['type']
                    
                    val_tuple = ('const', folded_val, value_type)
                    add_to_table(dest, val_tuple)
                    
                    new_instrs.append(new_instr)
                    continue
            
            arg_nums = [var2num[arg] for arg in instr['args']]
            
            # sort arguments for commutative operations
            if instr['op'] in COMMUTATIVE_OPS:
                arg_nums = sorted(arg_nums)
            
            val_tuple = (instr['op'], value_type) + tuple(arg_nums)
            
            found, num, var = find_existing_value(val_tuple)
            if found and dest not in overwritten and instr.get('op') != 'call':
                var2num[dest] = num
                new_instr = create_id_instruction(var, dest, instr.get('type'))
            else:
                add_to_table(dest, val_tuple)
                new_args = []
                for arg in instr['args']:
                    arg_num = var2num[arg]
                    _, canonical_arg = table[arg_num]
                    new_args.append(canonical_arg if canonical_arg is not None else arg)
                new_instr['args'] = new_args
        
        else:
            add_to_table(dest, ((instr['op'],), dest))
        
        new_instrs.append(new_instr)
    
    # remove self copies (v = id v)
    return [instr for instr in new_instrs 
            if not (instr.get('op') == 'id' and instr['args'][0] == instr['dest'])]

def main():
    prog = json.load(sys.stdin)

    for func in prog['functions']:
        blocks = form_blocks(func['instrs'])
        func['instrs'] = [instr for block in blocks for instr in lvn_block(block)]
    
    json.dump(prog, sys.stdout, indent=2)

if __name__ == '__main__':
    main()