from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .registry import Registry

BUDGETS={'compact':(3500,5000),'standard':(6000,8000),'complex':(9000,12000),'exceptional':(12000,15000)}

@dataclass
class ContextResult:
    text:str
    estimated_tokens:int
    included_ids:list[str]
    budget_class:str
    hard_limit:int

def build_context(root:Path,task_id:str,budget_class=None,max_hops=2,allow_draft=False):
    reg=Registry(root).scan()
    task=reg.by_id.get(task_id)
    if not task or task.object_type!='task':
        raise ValueError(f'task {task_id!r} not found')
    if task.status=='draft' and not allow_draft:
        raise RuntimeError('TASK_NOT_APPROVED: draft task cannot produce executable Builder context')
    if task.status not in {'draft','approved','active'}:
        raise RuntimeError(f'TASK_NOT_EXECUTABLE: status={task.status}')
    budget_class=budget_class or str(task.meta.get('budget_class') or 'standard')
    if budget_class not in BUDGETS:
        raise ValueError('unknown budget class')
    _,hard=BUDGETS[budget_class]
    selected=[task]
    seen={task_id}
    for key in ('findings','evidence','depends_on'):
        vals=task.meta.get(key,[])
        vals=[vals] if isinstance(vals,str) else vals
        for rid in vals or []:
            if rid in reg.by_id and rid not in seen:
                selected.append(reg.by_id[rid])
                seen.add(rid)
    inv=task.meta.get('invariants',[])
    inv=[inv] if isinstance(inv,str) else inv
    parts=[
        '# SportsBrain V1 Context Packet','',
        f'Task: {task_id}',f'Task status: {task.status}',f'Budget class: {budget_class}','',
        '## Governance','',
        'Use only this scoped task. External current source/runtime evidence outranks stale Memory. '
        'STOP on missing architecture decision or stop condition.','','## Task record','',
        (root/task.path).read_text(encoding='utf-8')
    ]
    if inv:
        parts += ['','## Required invariants','']+[f'- {x}' for x in inv]
    for o in selected[1:]:
        parts += ['',f'## {o.object_id}','',(root/o.path).read_text(encoding='utf-8')]
    sp=task.meta.get('source_paths',[])
    sp=[sp] if isinstance(sp,str) else sp
    parts += ['','## External source scope','']+[f'- `{x}`' for x in (sp or [])]
    text='\n'.join(parts).strip()+'\n'
    est=max(1,len(text)//4)
    if est>hard:
        raise RuntimeError(f'TASK_TOO_BROAD: estimated {est} > {hard}')
    return ContextResult(text,est,[o.object_id for o in selected if o.object_id],budget_class,hard)
