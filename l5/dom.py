import json
import sys

from cfg import *

def post_order(cfg, entry):
    visited = set()
    result = []
    
    def post_order_visit(bname):
        visited.add(bname)
        for succ in cfg[bname]['succs']:
          if succ not in visited:
              post_order_visit(succ)
        result.append(bname)

    post_order_visit(entry)
    return result

# block -> {dominators}
def dominators(name2block, cfg):
    entry = name2block[0][0]
    bnames = list(reversed(post_order(cfg, entry)))

    dom = {bname : {*bnames.copy()} for bname in bnames}
    dom[entry] = {entry}

    changed = True
    while changed:
        for bname in bnames:
            if bname == entry:
                continue

            prev = dom[bname]
            dom[bname] = set([bname]).union(
                set.intersection(*(dom[pred] for pred in cfg[bname]['preds']))
                )
            changed = dom[bname] == prev

    return dom

# dominator -> {blocks that it dominates} (invert dominators)
def dominated(dom):
    domed = {bname: set() for bname in dom}
    for bname, doms in dom.items():
        for dom_ in doms:
            domed[dom_].add(bname)

    return domed

# block -> {dominators} (*not* reflexive)
def strict_dominators(dom):
    sdom = {bname: set() for bname in dom}
    for bname in dom:
        sdom[bname] = {dom_ for dom_ in dom[bname] if dom_ != bname}

    return sdom

def dominance_tree(dom):
    sdom = strict_dominators(dom)

    tree = {bname: set() for bname in dom}
    for bname in sdom:
        non_idom = set().union(*(sdom[dtor] for dtor in sdom[bname]))
        idom = sdom[bname] - non_idom

        if idom:
            tree[idom.pop()].add(bname)

    return tree

def dominance_frontier(cfg, dom):
    sdom = strict_dominators(dom)

    frontier = {bname: set() for bname in dom}
    for bname in sdom:
        candidates = set().union(*(cfg[domed]['succs'] for domed in dominated(dom)[bname]))
        frontier[bname] = candidates - dominated(sdom)[bname]
    
    return frontier

def map_printer(m):
    return {k: sorted(list(v)) for k,v in m.items()}

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        name2block = block_map(form_blocks(func['instrs'])) 
        cfg = form_cfg(name2block)

        dom = dominators(name2block, cfg)

        match str(sys.argv[1]):
            case 'dom':
                json.dump(
                    map_printer(dom), sys.stdout, indent=2, sort_keys=True
                )
            case 'dom-tree':
                json.dump(
                    map_printer(dominance_tree(dom)), sys.stdout, indent=2, sort_keys=True
                )
            case 'dom-frontier':
                json.dump(
                    map_printer(dominance_frontier(cfg, dom)), sys.stdout, indent=2, sort_keys=True
                )
            
if __name__ == '__main__':
    main()
        