#!/usr/bin/env python3
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from memorylib.validate import validate, validate_runtime_payload
from memorylib.registry import Registry
from memorylib.graph import Graph
from memorylib.render import compile_shadow
from memorylib.dashboard import render_all
from memorylib.context import build_context
from memorylib.acceptance import run as acceptance_run, tree_fingerprint
from memorylib.v2 import build_context_packets, ingest_events
from memorylib.live import render_live_status
from memorylib.observer import (
    FixtureGitHubClient,
    GitHubClient,
    ingest_handoff,
    observe_and_write,
    observe_sources,
    parse_builder_handoff,
    write_runtime_outputs,
)
from memorylib.semantic_graph import (
    build_semantic_graph,
    semantic_graph_health,
    validate_semantic_graph,
)

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
    sp.add_parser('packets')
    o=sp.add_parser('observe')
    o.add_argument('--vault',required=True)
    o.add_argument('--repository',action='append',dest='repositories')
    o.add_argument('--fixture')
    o.add_argument('--dry-run',action='store_true')
    h=sp.add_parser('ingest-handoff')
    h.add_argument('input')
    h.add_argument('--vault',required=True)
    vc=sp.add_parser('validate-candidates')
    vc.add_argument('path')
    u=sp.add_parser('update')
    u.add_argument('payload')
    u.add_argument('--commit',action='store_true')
    u.add_argument('--commit-message',default='memory: apply canonical V2 update')
    l=sp.add_parser('live')
    l.add_argument('--source-repo',required=True)
    l.add_argument('--vault',required=True)
    c=sp.add_parser('context')
    c.add_argument('task_id')
    c.add_argument('--allow-draft',action='store_true')
    c.add_argument('--output')
    graph = sp.add_parser('graph')
    graph_sp = graph.add_subparsers(dest='graph_cmd', required=True)
    graph_build = graph_sp.add_parser('build')
    graph_build.add_argument('--vault')
    graph_build.add_argument('--include-runtime', action='store_true')
    graph_validate = graph_sp.add_parser('validate')
    graph_validate.add_argument('--graph-root')
    graph_health = graph_sp.add_parser('health')
    graph_health.add_argument('--graph-root')
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
    if a.cmd=='packets':
        print(json.dumps(build_context_packets(ROOT),indent=2,sort_keys=True))
        return 0
    if a.cmd=='update':
        import subprocess
        data=json.loads(Path(a.payload).read_text(encoding='utf-8'))
        result=ingest_events(ROOT,data.get('events',[]),canonical_records=data.get('canonical_records',[]),validate_after=False)
        render_all(ROOT)
        report=validate(ROOT,'v1')
        if report.errors:
            print(json.dumps(report.to_dict(),indent=2,sort_keys=True)); return 1
        if a.commit:
            paths=['00_HOME.md','CURRENT_STATE.md','CURRENT_PRIORITIES.md','CURRENT_BLOCKERS.md','CURRENT_TASK.md','findings/OPEN.md','findings/RESOLVED.md','views','mocs','builder/CURRENT_CONTEXT_PACKET.md','builder/context','events','decisions/records','workstreams','tasks/records','findings/records','state/records','architecture','_meta']
            subprocess.run(['git','-C',str(ROOT),'add','--',*paths],check=True)
            subprocess.run(['git','-C',str(ROOT),'commit','-m',a.commit_message],check=True)
        print(json.dumps({'results':[r.__dict__ for r in result],'committed':a.commit,'errors':report.errors,'warnings':report.warnings},indent=2))
        return 0
    if a.cmd=='live':
        print(json.dumps(render_live_status(ROOT,Path(a.vault),Path(a.source_repo)),indent=2,sort_keys=True))
        return 0
    if a.cmd=='observe':
        client=GitHubClient()
        if a.fixture:
            client=FixtureGitHubClient(json.loads(Path(a.fixture).read_text(encoding='utf-8')))
        vault=Path(a.vault)
        previous={}
        previous_path=vault/'_live'/'SOURCE_OBSERVER.json'
        if previous_path.exists():
            try: previous=json.loads(previous_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError: previous={}
        handoff_path=vault/'_live'/'BUILDER_HANDOFFS.json'
        if handoff_path.exists():
            try:
                handoff_store=json.loads(handoff_path.read_text(encoding='utf-8'))
                if isinstance(handoff_store,dict) and isinstance(handoff_store.get('candidates'),list):
                    previous['builder_handoffs']=handoff_store['candidates']
            except json.JSONDecodeError:
                pass
        payload=observe_sources(ROOT,client,repositories=a.repositories,previous=previous)
        if not a.dry_run:
            write_runtime_outputs(vault,payload)
        print(json.dumps(payload,indent=2,sort_keys=True))
        return 0
    if a.cmd=='ingest-handoff':
        text=Path(a.input).read_text(encoding='utf-8')
        evidence=parse_builder_handoff(text)
        result=ingest_handoff(Path(a.vault)/'_live'/'BUILDER_HANDOFFS.json',evidence)
        print(json.dumps(result,indent=2,sort_keys=True))
        return 0
    if a.cmd=='validate-candidates':
        errors=validate_runtime_payload(Path(a.path))
        print(json.dumps({'errors':errors,'error_count':len(errors)},indent=2,sort_keys=True))
        return 1 if errors else 0
    if a.cmd=='acceptance':
        r=acceptance_run(ROOT)
        print(json.dumps(r,indent=2,sort_keys=True))
        return 0 if r['ok'] else 1
    if a.cmd=='graph':
        if a.graph_cmd=='build':
            vault = Path(a.vault) if a.vault else None
            result = build_semantic_graph(
                ROOT,
                vault=vault,
                include_runtime=bool(a.include_runtime or vault),
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        graph_root = Path(a.graph_root) if a.graph_root else None
        if a.graph_cmd=='validate':
            result = validate_semantic_graph(ROOT, graph_root)
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            return 1 if result.errors or result.warnings else 0
        if a.graph_cmd=='health':
            print(json.dumps(semantic_graph_health(ROOT, graph_root), indent=2, sort_keys=True))
            return 0

if __name__=='__main__':
    raise SystemExit(main())
