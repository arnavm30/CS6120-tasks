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
        changed = False
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

def brute_force_dominators(cfg, entry):    
    def enumerate_paths(bname, current, all_paths, target, visited_edges):
        current.append(bname)

        if bname == target:
            all_paths.append(set(current))
        else:
            for succ in cfg.get(bname, {}).get('succs', []):
                edge = (bname, succ)
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    enumerate_paths(succ, current, all_paths, target, visited_edges)
                    visited_edges.remove(edge)

        current.pop()

    all_paths_to_bname = {bname: [] for bname in cfg}
    for bname in cfg:
        if bname == entry:
            all_paths_to_bname[bname] = [{entry}] 
        else:
            paths = []
            enumerate_paths(entry, [], paths, bname, set())
            all_paths_to_bname[bname] = paths

    dom = {}
    for bname in cfg:
        if bname == entry:
            dom[bname] = {entry}
        elif all_paths_to_bname[bname]:
            dom[bname] = set.intersection(*all_paths_to_bname[bname])
        else:
            dom[bname] = set()

    return dom

def remove_unreachable(cfg, entry):
    def reachable(cfg, entry):
        visited = set()

        def dfs(bname):
            if bname in visited:
                return
            visited.add(bname)
            for succ in cfg[bname]['succs']:
                dfs(succ)

        dfs(entry)
        return visited
    
    reachable = reachable(cfg, entry)
    for bname in cfg.copy():
        if bname not in reachable:
            cfg.pop(bname)
    for bname in cfg.copy():
        cfg[bname]['preds'] = [pred for pred in cfg[bname]['preds'] if pred in cfg]

    return cfg

def map_printer(m):
    return {k: sorted(list(v)) for k,v in m.items()}

def main():
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        name2block = block_map(form_blocks(func['instrs'])) 
        cfg = form_cfg(name2block)
        remove_unreachable(cfg, name2block[0][0])

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
            case 'dom-bf':
                json.dump(
                    map_printer(brute_force_dominators(cfg, name2block[0][0])), sys.stdout, indent=2, sort_keys=True
                )
                
if __name__ == '__main__':
    main()
        