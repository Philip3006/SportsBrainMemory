#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from memorylib.validate import validate
from memorylib.registry import Registry
from memorylib.graph import Graph
from memorylib.render import compile_shadow
from memorylib.dashboard import render_all
from memorylib.context import build_context
from memorylib.acceptance import run as acceptance_run, tree_fingerprint

def main():
    p=argparse.ArgumentParser()
    sp=p.add_subparsers(dest='cmd',required=True)
    v=sp.add_parser('validate')
    v.add_argument('--profile',default='v1',choices=['v1','v0-compatible'])
    sp.add_parser('render')
    sp.add_parser('compile')
    sp.add_parser('health')
    sp.add_parser('acceptance')
    sp.add_parser('fingerprint')
    c=sp.add_parser('context')
    c.add_argument('task_id')
    c.add_argument('--allow-draft',action='store_true')
    c.add_argument('--output')
    a=p.parse_args()

    if a.cmd=='validate':
        r=validate(ROOT,a.profile)
        print(json.dumps(r.to_dict(),indent=2,sort_keys=True))
        return 1 if r.errors or r.warnings else 0
    if a.cmd=='render':
        print(json.dumps(render_all(ROOT),indent=2))
        return 0
    if a.cmd=='compile':
        reg=Registry(ROOT).scan()
        out=compile_shadow(ROOT,reg,Graph(reg).build())
        print(out)
        return 0
    if a.cmd=='health':
        r=validate(ROOT,'v1')
        score=max(0,10-r.errors*2-r.warnings*.25)
        print(json.dumps({'memory_health_score':score,'errors':r.errors,'warnings':r.warnings,'diagnostic_only':True},indent=2))
        return 1 if r.errors else 0
    if a.cmd=='context':
        r=build_context(ROOT,a.task_id,allow_draft=a.allow_draft)
        if a.output:
            (ROOT/a.output).write_text(r.text,encoding='utf-8')
        else:
            print(r.text)
        print(json.dumps({'estimated_tokens':r.estimated_tokens,'hard_limit':r.hard_limit,'included_ids':r.included_ids},indent=2),file=sys.stderr)
        return 0
    if a.cmd=='fingerprint':
        print(tree_fingerprint(ROOT))
        return 0
    if a.cmd=='acceptance':
        r=acceptance_run(ROOT)
        print(json.dumps(r,indent=2,sort_keys=True))
        return 0 if r['ok'] else 1

if __name__=='__main__':
    raise SystemExit(main())
