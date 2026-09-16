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
from memorylib.context_compiler import (
    ContextRequest,
    build_context_atomic,
    compile_context,
    inspect_context_pack,
    validate_context_pack,
)
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
    context_sp=c.add_subparsers(dest='context_cmd', required=True)
    context_build=context_sp.add_parser('build')
    context_build.add_argument('--consumer', required=True)
    context_build.add_argument('--builder-number', type=int)
    context_build.add_argument('--task', default='')
    context_build.add_argument('--workstream', default='')
    context_build.add_argument('--repository', action='append', dest='repository_scope')
    context_build.add_argument('--seed', action='append', dest='entity_seeds')
    context_build.add_argument('--domain', action='append', dest='requested_domains')
    context_build.add_argument('--budget-tokens', type=int, default=6000)
    context_build.add_argument('--max-entities', type=int, default=80)
    context_build.add_argument('--freshness', default='ANY', choices=['ANY', 'FRESH_ONLY', 'FRESH_OR_AGING'])
    context_build.add_argument('--include-runtime', action='store_true')
    context_build.add_argument('--vault')
    context_build.add_argument('--request-id')
    context_build.add_argument('--request-json')
    context_build.add_argument('--json', action='store_true', dest='json_output')
    context_validate=context_sp.add_parser('validate')
    context_validate.add_argument('path')
    context_inspect=context_sp.add_parser('inspect')
    context_inspect.add_argument('path')
    context_legacy=context_sp.add_parser('legacy')
    context_legacy.add_argument('task_id')
    context_legacy.add_argument('--allow-draft',action='store_true')
    context_legacy.add_argument('--output')
    graph = sp.add_parser('graph')
    graph_sp = graph.add_subparsers(dest='graph_cmd', required=True)
    graph_build = graph_sp.add_parser('build')
    graph_build.add_argument('--vault')
    graph_build.add_argument('--include-runtime', action='store_true')
    graph_build.add_argument('--output-root')
    graph_validate = graph_sp.add_parser('validate')
    graph_validate.add_argument('--graph-root')
    graph_validate.add_argument('--vault')
    graph_health = graph_sp.add_parser('health')
    graph_health.add_argument('--graph-root')
    graph_health.add_argument('--vault')
    argv=sys.argv[1:]
    # Preserve the pre-V3 shorthand: ``memory.py context TASK-ID``.
    if len(argv) >= 2 and argv[0] == 'context' and argv[1] not in {'build', 'validate', 'inspect', 'legacy', '-h', '--help'}:
        argv=[argv[0], 'legacy', *argv[1:]]
    a=p.parse_args(argv)

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
        if a.context_cmd=='legacy':
            r=build_context(ROOT,a.task_id,allow_draft=a.allow_draft)
            if a.output:
                (ROOT/a.output).write_text(r.text,encoding='utf-8')
            else:
                print(r.text)
            print(json.dumps({'estimated_tokens':r.estimated_tokens,'hard_limit':r.hard_limit,'included_ids':r.included_ids},indent=2),file=sys.stderr)
            return 0
        if a.context_cmd=='validate':
            print(json.dumps({'valid': True, 'pack': validate_context_pack(Path(a.path))}, indent=2, sort_keys=True))
            return 0
        if a.context_cmd=='inspect':
            print(json.dumps(inspect_context_pack(Path(a.path)), indent=2, sort_keys=True))
            return 0
        if a.request_json:
            request_data=json.loads(Path(a.request_json).read_text(encoding='utf-8'))
        else:
            request_data={
                'request_id': a.request_id,
                'consumer_type': a.consumer,
                'builder_number': a.builder_number,
                'task': a.task,
                'workstream': a.workstream,
                'repository_scope': a.repository_scope or [],
                'entity_seeds': a.entity_seeds or [],
                'requested_domains': a.requested_domains or [],
                'token_budget': a.budget_tokens,
                'max_entity_count': a.max_entities,
                'freshness_requirement': a.freshness,
                'include_runtime': a.include_runtime,
            }
        request=ContextRequest.from_mapping(request_data)
        vault=Path(a.vault) if a.vault else None
        if vault:
            result=build_context_atomic(ROOT, request, vault=vault)
            payload=result['pack']
            markdown=Path(result['markdown']).read_text(encoding='utf-8')
        else:
            compilation=compile_context(ROOT, request)
            payload=compilation.pack
            markdown=compilation.markdown
        if a.json_output:
            print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(markdown)
            print(json.dumps({'context_digest': payload['context_digest'], 'estimated_tokens': payload['estimated_tokens'], 'included_entity_count': payload['included_entity_count'], 'output': result.get('json') if vault else None}, indent=2, sort_keys=True), file=sys.stderr)
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
                output_root=Path(a.output_root) if a.output_root else None,
            )
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        graph_root = Path(a.graph_root) if a.graph_root else None
        if a.graph_cmd=='validate':
            vault = Path(a.vault) if a.vault else None
            result = validate_semantic_graph(ROOT, graph_root, vault=vault)
            print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
            return 1 if result.errors or result.warnings else 0
        if a.graph_cmd=='health':
            vault = Path(a.vault) if a.vault else None
            print(json.dumps(semantic_graph_health(ROOT, graph_root, vault=vault), indent=2, sort_keys=True))
            return 0

if __name__=='__main__':
    raise SystemExit(main())
