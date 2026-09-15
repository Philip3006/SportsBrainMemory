from __future__ import annotations
from pathlib import Path
import tempfile, shutil, time, hashlib
from .validate import validate
from .registry import Registry
from .dashboard import render_all
from .context import build_context

def tree_fingerprint(root:Path):
    h=hashlib.sha256()
    excludes={'.memory-build','__pycache__','.git','.memory-backups','.claude','.obsidian'}
    metadata_excludes={'_meta/ACCEPTANCE_REPORT.json','_meta/PACKAGE_MANIFEST.json','.DS_Store'}
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if not p.is_file() or any(x in excludes for x in rel.parts) or p.suffix=='.pyc' or rel.as_posix() in metadata_excludes:
            continue
        h.update(str(p.relative_to(root)).encode())
        h.update(b'\0')
        h.update(p.read_bytes())
        h.update(b'\0')
    return h.hexdigest()

def run(root:Path):
    gates=[]
    render_all(root)
    gates.append(('render_generated_views',True,''))
    p2=tree_fingerprint(root)
    render_all(root)
    p3=tree_fingerprint(root)
    gates.append(('generated_views_idempotent',p2==p3,f'{p2} != {p3}' if p2!=p3 else ''))

    r=validate(root,'v1')
    gates.append(('strict_validator',r.errors==0 and r.warnings==0,f'errors={r.errors} warnings={r.warnings}'))

    graph_manifest = root / 'views' / 'graph' / 'GRAPH_MANIFEST.json'
    if graph_manifest.exists():
        from .semantic_graph import validate_semantic_graph
        graph_report = validate_semantic_graph(root)
        gates.append(('semantic_graph_integrity', graph_report.errors == 0 and graph_report.warnings == 0, f'errors={graph_report.errors} warnings={graph_report.warnings}'))

    reg=Registry(root).scan()
    drafts=[o for o in reg.objects if o.object_type=='task' and o.status=='draft']
    ctx_ok=True
    details=[]
    for o in drafts:
        try:
            try:
                build_context(root,o.object_id)
                ctx_ok=False
                details.append(f'{o.object_id}:draft executable unexpectedly')
            except RuntimeError as e:
                if 'TASK_NOT_APPROVED' not in str(e):
                    raise
            c=build_context(root,o.object_id,allow_draft=True)
            details.append(f'{o.object_id}:{c.estimated_tokens}/{c.hard_limit}')
        except Exception as e:
            ctx_ok=False
            details.append(f'{o.object_id}:ERR:{e}')
    gates.append(('task_context_contracts',ctx_ok,'; '.join(details)))

    active_tasks=[o for o in reg.objects if o.object_type=='task' and o.status in {'approved','active'}]
    n_active=len(active_tasks)
    ctext=(root/'CURRENT_TASK.md').read_text(encoding='utf-8')
    if n_active==0:
        task_ok='**NONE**' in ctext
        task_detail='' if task_ok else 'CURRENT_TASK should say NONE for idle state'
    elif n_active==1:
        t=active_tasks[0]
        task_ok=t.object_id in ctext
        task_detail='' if task_ok else f'CURRENT_TASK should reference {t.object_id}'
    else:
        task_ok=False
        task_detail=f'multiple active tasks: {[o.object_id for o in active_tasks]}'
    gates.append(('builder_lifecycle_consistent',task_ok and n_active<=1,task_detail))
    if n_active==1:
        t=active_tasks[0]
        try:
            build_context(root,t.object_id)
            approved_ok=True
            approved_detail=t.object_id
        except Exception as e:
            approved_ok=False
            approved_detail=str(e)
        gates.append(('approved_task_executable',approved_ok,approved_detail))

    p0=(root/'workstreams/P0-A.md').read_text(encoding='utf-8')
    gates.append(('p0a_closed','status: closed' in p0 and 'EVD-P0A-PROD-001' in p0,''))

    st=reg.by_id.get('STATE-20260816-001')
    sep=bool(st and st.meta.get('source_release_sha')!=st.meta.get('runtime_data_head'))
    gates.append(('source_runtime_provenance_separate',sep,''))

    td=Path(tempfile.mkdtemp(prefix='sbmem-scale-'))
    try:
        (td/'objects').mkdir()
        for i in range(5000):
            (td/'objects'/f'{i:04d}.md').write_text(
                f'---\nid: SYN-{i:05d}\ntype: component\nstatus: active\n---\n# Synthetic\n',
                encoding='utf-8'
            )
        t=time.perf_counter()
        rr=Registry(td).scan()
        elapsed=time.perf_counter()-t
        gates.append(('scale_5000',len(rr.by_id)==5000 and elapsed<8.0,f'{elapsed:.3f}s ids={len(rr.by_id)}'))
    finally:
        shutil.rmtree(td,ignore_errors=True)

    ok=all(x[1] for x in gates)
    return {
        'ok':ok,
        'gates':[{'name':n,'ok':o,'detail':d} for n,o,d in gates],
        'fingerprint':tree_fingerprint(root),
        'validator':r.to_dict()
    }
