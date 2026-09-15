from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import json
import re
from .registry import Registry, RegistryIssue
from .graph import Graph
from .schema import SchemaStore, validate_meta
from .v2 import FROZEN_RESEARCH_SHA, V1_GENERATED_MARKER, V2_GENERATED_MARKER, freshness_state, parse_timestamp, read_manifest, validate_event
from .frontmatter import parse_frontmatter
from .observer import validate_blocker, validate_candidate, validate_handoff_evidence

@dataclass
class ValidationReport:
    profile:str
    issues:list[RegistryIssue]
    object_count:int
    id_count:int
    status_counts:dict[str,int]
    @property
    def errors(self):
        return sum(1 for i in self.issues if i.severity in {'FATAL','ERROR'})
    @property
    def warnings(self):
        return sum(1 for i in self.issues if i.severity=='WARNING')
    def to_dict(self):
        return {
            'profile':self.profile,'errors':self.errors,'warnings':self.warnings,
            'object_count':self.object_count,'id_count':self.id_count,
            'status_counts':self.status_counts,'issues':[asdict(i) for i in self.issues]
        }


def validate_runtime_payload(path: Path) -> list[str]:
    """Validate non-canonical observer, candidate, blocker, or handoff JSON."""
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return [f'{path}: invalid JSON: {exc}']
    if not isinstance(payload, dict) or payload.get('schema') != 1:
        return [f'{path}: runtime payload schema must be 1']
    errors: list[str] = []
    candidates = payload.get('candidates', [])
    if not isinstance(candidates, list):
        errors.append(f'{path}: candidates must be a list')
    else:
        ids: set[str] = set()
        for index, candidate in enumerate(candidates):
            try:
                if candidate.get('candidate_type') == 'CANDIDATE_OPERATIONAL_EVIDENCE':
                    validate_handoff_evidence(candidate)
                else:
                    validate_candidate(candidate)
                candidate_id = candidate.get('candidate_id')
                if candidate_id in ids:
                    errors.append(f'{path}: duplicate candidate_id {candidate_id}')
                ids.add(candidate_id)
            except Exception as exc:
                errors.append(f'{path}: candidates[{index}]: {exc}')
    blockers = payload.get('blockers', [])
    if blockers is not None:
        if not isinstance(blockers, list):
            errors.append(f'{path}: blockers must be a list')
        else:
            for index, blocker in enumerate(blockers):
                try:
                    validate_blocker(blocker)
                except Exception as exc:
                    errors.append(f'{path}: blockers[{index}]: {exc}')
    return errors

def _structured(path:str)->bool:
    return path.startswith((
        'state/records/','tasks/records/','findings/records/','decisions/records/',
        'components/','jobs/','writers/','models/','datasets/','providers/',
        'evidence/records/','verifications/records/','tests/records/','workstreams/'
    ))


def _validate_v2(root:Path, issues:list[RegistryIssue]):
    manifest_path=root/'_meta'/'MEMORY_V2.json'
    if not manifest_path.exists():
        issues.append(RegistryIssue('ERROR','MISSING_MEMORY_V2_MANIFEST','_meta/MEMORY_V2.json is required'))
        return
    try:
        manifest=read_manifest(root)
        required={'memory_version','schema_version','source_main_sha','source_latest_meaningful_sha','source_latest_meaningful_at','canonical_updated_at','canonical_status','builder_platform'}
        missing=sorted(required-set(manifest))
        if missing:
            issues.append(RegistryIssue('ERROR','MEMORY_V2_MANIFEST_FIELD',f'missing manifest field(s): {", ".join(missing)}','_meta/MEMORY_V2.json'))
        for key in ('source_main_sha','source_latest_meaningful_sha'):
            if not re.fullmatch(r'[0-9a-f]{40}',str(manifest.get(key,''))):
                issues.append(RegistryIssue('ERROR','MEMORY_V2_BAD_SHA',f'{key} must be a 40-character lowercase SHA','_meta/MEMORY_V2.json'))
        expected=freshness_state(manifest['canonical_updated_at'],manifest['source_latest_meaningful_at'])
        if manifest.get('canonical_status') != expected:
            issues.append(RegistryIssue('ERROR','MEMORY_V2_FRESHNESS_DRIFT',f"manifest says {manifest.get('canonical_status')}, computed {expected}",'_meta/MEMORY_V2.json'))
        if manifest.get('builder_platform') != 'CODEX':
            issues.append(RegistryIssue('ERROR','BUILDER_PLATFORM_DRIFT','CODEX must be the sole builder platform','_meta/MEMORY_V2.json'))
        if manifest.get('frozen_research_sha') != FROZEN_RESEARCH_SHA:
            issues.append(RegistryIssue('ERROR','FROZEN_RESEARCH_SHA_DRIFT','manifest frozen_research_sha does not match the CEO-approved Research SHA','_meta/MEMORY_V2.json'))
        if manifest.get('builder_roles') != {
            '1': 'Top-5 Shadow Integration',
            '2': 'Top-5 Production / Activation Readiness',
            '3': 'Memory / Obsidian / Observability',
        }:
            issues.append(RegistryIssue('ERROR','BUILDER_ROLE_DRIFT','manifest builder_roles must be the numbered current ownership map','_meta/MEMORY_V2.json'))
    except Exception as exc:
        issues.append(RegistryIssue('ERROR','MEMORY_V2_MANIFEST_INVALID',str(exc),'_meta/MEMORY_V2.json'))

    ids={}
    for bucket,canonical in (('records',True),('pending',False)):
        directory=root/'events'/bucket
        if not directory.exists():
            issues.append(RegistryIssue('ERROR','MISSING_EVENT_DIRECTORY',f'events/{bucket} is required',f'events/{bucket}'))
            continue
        for path in sorted(directory.glob('*.json')):
            try:
                event=json.loads(path.read_text(encoding='utf-8'))
                normalized=validate_event(event,canonical=canonical)
                if bool(normalized.get('canonical')) != canonical:
                    issues.append(RegistryIssue('ERROR','EVENT_CANONICAL_BUCKET','event canonical flag disagrees with its directory',str(path.relative_to(root))))
                event_id=normalized['event_id']
                if event_id in ids:
                    issues.append(RegistryIssue('ERROR','DUPLICATE_EVENT_ID',f'{event_id} also exists at {ids[event_id]}',str(path.relative_to(root))))
                ids[event_id]=str(path.relative_to(root))
                if canonical and not normalized.get('evidence'):
                    issues.append(RegistryIssue('ERROR','CANONICAL_EVENT_NO_EVIDENCE',f'{event_id} has no evidence',str(path.relative_to(root))))
            except Exception as exc:
                issues.append(RegistryIssue('ERROR','EVENT_SCHEMA_INVALID',str(exc),str(path.relative_to(root))))

    current_role_paths = [
        '00_HOME.md', 'CURRENT_STATE.md', 'CURRENT_PRIORITIES.md', 'CURRENT_BLOCKERS.md',
        'CURRENT_TASK.md', 'README.md', 'SETUP.md', 'builder/START_HERE.md',
        'builder/CODEX_START_HERE.md', 'builder/CURRENT_CONTEXT_PACKET.md',
        'workstreams/TOP5-RESEARCH.md', 'workstreams/TOP5-PRODUCTION.md',
        'workstreams/TOP5-SHADOW-READINESS.md', 'workstreams/TOP5-SHADOW-INTEGRATION.md',
        'workstreams/TOP5-ACTIVATION-READINESS.md', 'workstreams/MEMORY-V2.md',
        'tasks/records/TASK-MEM-V2-001.md', 'decisions/records/DEC-0023.md',
    ]
    current_role_paths.extend(str(p.relative_to(root)) for p in sorted((root / 'builder' / 'context').glob('*.md')))
    for rel in current_role_paths:
        path = root / rel
        if not path.exists():
            issues.append(RegistryIssue('ERROR','MISSING_CURRENT_GOVERNANCE_FILE',rel,rel))
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        if re.search(r'\bBuilder [ABC]\b|BUILDER_[ABC](?:_|\.)', text):
            issues.append(RegistryIssue('ERROR','LEGACY_BUILDER_NAMING',f'current operational file uses legacy alphabetical builder naming: {rel}',rel))

    packet_headers = {
        'BUILDER_1_SHADOW_INTEGRATION.md': 'BUILDER: 1',
        'BUILDER_2_ACTIVATION_READINESS.md': 'BUILDER: 2',
        'BUILDER_3_MEMORY.md': 'BUILDER: 3',
    }
    for filename, header in packet_headers.items():
        path = root / 'builder' / 'context' / filename
        if path.exists():
            first_line = path.read_text(encoding='utf-8', errors='replace').splitlines()[0] if path.read_text(encoding='utf-8', errors='replace').splitlines() else ''
            if first_line.strip() != header:
                issues.append(RegistryIssue('ERROR','BUILDER_HANDOFF_NUMBER_MISSING',f'{filename} must begin with {header}',str(path.relative_to(root))))

    research_path = root / 'workstreams' / 'TOP5-RESEARCH.md'
    if research_path.exists():
        research_text = research_path.read_text(encoding='utf-8', errors='replace')
        if 'status: completed_ceo_approved' not in research_text or FROZEN_RESEARCH_SHA not in research_text:
            issues.append(RegistryIssue('ERROR','RESEARCH_GATE_NOT_CURRENT','Top-5 Research must be CEO approved and frozen at the authoritative SHA',str(research_path.relative_to(root))))
        if 'final_audit_active' in research_text:
            issues.append(RegistryIssue('ERROR','RESEARCH_GATE_STALE','final_audit_active cannot be the current Research state',str(research_path.relative_to(root))))
    research_event = root / 'events' / 'records' / 'EVT-20260913-010.json'
    if not research_event.exists():
        issues.append(RegistryIssue('ERROR','RESEARCH_COMPLETION_EVENT_MISSING','EVT-20260913-010 is required for the CEO-approved Research Gate',str(research_event.relative_to(root))))
    else:
        try:
            payload = json.loads(research_event.read_text(encoding='utf-8'))
            if payload.get('source_sha') != FROZEN_RESEARCH_SHA or payload.get('verification_state') != 'ceo_approved':
                issues.append(RegistryIssue('ERROR','RESEARCH_COMPLETION_EVENT_INVALID','Research completion event must carry the frozen SHA and CEO approval',str(research_event.relative_to(root))))
        except Exception as exc:
            issues.append(RegistryIssue('ERROR','RESEARCH_COMPLETION_EVENT_INVALID',str(exc),str(research_event.relative_to(root))))

    expected_workstream_owners = {
        'workstreams/TOP5-SHADOW-INTEGRATION.md': ('Builder 1', '1'),
        'workstreams/TOP5-ACTIVATION-READINESS.md': ('Builder 2', '2'),
        'workstreams/MEMORY-V2.md': ('Builder 3', '3'),
    }
    for rel, (owner, number) in expected_workstream_owners.items():
        path = root / rel
        if not path.exists():
            issues.append(RegistryIssue('ERROR','CURRENT_WORKSTREAM_MISSING',rel,rel))
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        if f'builder: {owner}' not in text or f'builder_number: {number}' not in text:
            issues.append(RegistryIssue('ERROR','CURRENT_WORKSTREAM_OWNER_DRIFT',f'{rel} must be owned by {owner}',rel))

    merged_pr_event = root / 'events' / 'records' / 'EVT-20260913-008.json'
    if merged_pr_event.exists():
        try:
            payload = json.loads(merged_pr_event.read_text(encoding='utf-8'))
            if payload.get('type') != 'PR_MERGED' or payload.get('verification_state') != 'merged_source' or payload.get('source_sha') != '16be9cdb4d7fd84b1a18f708e210693f164268c3':
                issues.append(RegistryIssue('ERROR','PR56_MERGE_STATE_REGRESSION','PR #56 must remain represented as merged with the approved head',str(merged_pr_event.relative_to(root))))
        except Exception as exc:
            issues.append(RegistryIssue('ERROR','PR56_MERGE_STATE_INVALID',str(exc),str(merged_pr_event.relative_to(root))))
    else:
        issues.append(RegistryIssue('ERROR','PR56_MERGE_EVENT_MISSING','EVT-20260913-008 is required',str(merged_pr_event.relative_to(root))))

    current_text = '\n'.join((root / rel).read_text(encoding='utf-8', errors='replace') for rel in ('00_HOME.md','CURRENT_STATE.md','CURRENT_PRIORITIES.md','CURRENT_BLOCKERS.md') if (root / rel).exists())
    if FROZEN_RESEARCH_SHA not in current_text or 'EVT-20260913-010' not in current_text:
        issues.append(RegistryIssue('ERROR','CURRENT_RESEARCH_VIEW_DRIFT','generated current views must reference the latest Research completion event and frozen SHA'))
    if '2425' not in current_text or '2526' not in current_text or 'SEALED' not in current_text:
        issues.append(RegistryIssue('ERROR','SEALED_STATUS_DRIFT','current views must preserve SEALED status for 2425 and 2526'))
    if 'NOT APPROVED' not in current_text:
        issues.append(RegistryIssue('ERROR','TOP5_ACTIVATION_STATUS_HIDDEN','current views must show that Top-5 live activation is not approved'))

    generated_paths=['00_HOME.md','CURRENT_STATE.md','CURRENT_PRIORITIES.md','CURRENT_BLOCKERS.md','CURRENT_TASK.md']
    try:
        manifest=read_manifest(root)
        for rel in generated_paths:
            path=root/rel
            if not path.exists():
                issues.append(RegistryIssue('ERROR','MISSING_CURRENT_VIEW',rel,rel)); continue
            text=path.read_text(encoding='utf-8')
            if V2_GENERATED_MARKER not in text or V1_GENERATED_MARKER not in text:
                issues.append(RegistryIssue('ERROR','V2_GENERATED_VIEW_MARKER',f'{rel} missing V1/V2 generated markers',rel))
            if str(manifest.get('source_main_sha')) not in text and rel != 'CURRENT_TASK.md':
                issues.append(RegistryIssue('ERROR','STALE_CURRENT_VIEW',f'{rel} does not reference audited source SHA',rel))
        if manifest.get('canonical_status') == 'STALE' and 'STALE' not in (root/'CURRENT_STATE.md').read_text(encoding='utf-8'):
            issues.append(RegistryIssue('ERROR','STALE_CURRENT_STATE_HIDDEN','stale Memory must be visible in CURRENT_STATE.md','CURRENT_STATE.md'))
        active=[o for o in Registry(root).scan().objects if o.object_type=='task' and o.status in {'approved','active'}]
        task_text=(root/'CURRENT_TASK.md').read_text(encoding='utf-8')
        if len(active)==1 and active[0].object_id not in task_text:
            issues.append(RegistryIssue('ERROR','CURRENT_TASK_VIEW_DRIFT',f'{active[0].object_id} missing from CURRENT_TASK.md','CURRENT_TASK.md'))
    except Exception:
        pass

    governance_files=['CLAUDE.md','builder/START_HERE.md','builder/CLAUDE_RUNBOOK.md','SETUP.md']
    retired_phrases=('Claude is the normal Builder','Claude is the normal Builder/source mutator','Claude Code is the active builder')
    for rel in governance_files:
        path=root/rel
        if path.exists() and any(phrase in path.read_text(encoding='utf-8') for phrase in retired_phrases):
            issues.append(RegistryIssue('ERROR','RETIRED_CLAUDE_WORKFLOW',f'active Claude builder assumption remains in {rel}',rel))

    for path in root.rglob('*.md'):
        if any(part in {'.git','.memory-build','.memory-backups','_live'} for part in path.relative_to(root).parts):
            continue
        try:
            meta,_=parse_frontmatter(path.read_text(encoding='utf-8'))
        except Exception:
            continue
        for key,value in meta.items():
            if key.endswith('_at') or key in {'last_updated','last_verified','generated_at'}:
                if isinstance(value,str):
                    try: parse_timestamp(value,key)
                    except Exception as exc: issues.append(RegistryIssue('ERROR','INVALID_TIMESTAMP',str(exc),str(path.relative_to(root))))

def validate(root:Path,profile='v1'):
    reg=Registry(root).scan()
    graph=Graph(reg).build()
    issues=[*reg.issues,*graph.issues]
    _validate_v2(root,issues)
    store=SchemaStore(root/'_meta'/'schemas')

    for o in reg.objects:
        if not o.object_type:
            if profile=='v1' and _structured(o.relpath):
                issues.append(RegistryIssue('ERROR','MISSING_TYPE','structured object missing type',o.relpath))
            continue
        schema=store.get(o.object_type)
        if schema:
            for s in validate_meta(o.meta,schema):
                sev=s.severity
                if s.code=='SCHEMA_UNKNOWN_FIELD':
                    sev='WARNING'
                issues.append(RegistryIssue(sev,s.code,s.message,o.relpath))
        elif profile=='v1' and _structured(o.relpath):
            if not o.status:
                issues.append(RegistryIssue('ERROR','MISSING_STATUS','structured object missing status',o.relpath))

    states=[o for o in reg.objects if o.object_type=='project-state' and o.status=='current']
    if len(states)!=1:
        issues.append(RegistryIssue('ERROR','CURRENT_STATE_CARDINALITY',f'expected 1 current project-state, got {len(states)}'))

    active=[o for o in reg.objects if o.object_type=='task' and o.status in {'approved','active'}]
    if len(active)>1:
        issues.append(RegistryIssue('ERROR','MULTIPLE_ACTIVE_TASKS',','.join(o.object_id or o.relpath for o in active)))

    by_id=reg.by_id
    for view,should_open in [('findings/OPEN.md',True),('findings/RESOLVED.md',False)]:
        p=root/view
        if not p.exists():
            issues.append(RegistryIssue('ERROR','MISSING_GENERATED_VIEW',view))
            continue
        ids=re.findall(r'FND-\d{8}-\d{3}',p.read_text(encoding='utf-8'))
        for fid in ids:
            o=by_id.get(fid)
            if not o:
                continue
            is_open=o.status in {'open','observed','confirmed','accepted','in_progress','resolved_candidate'}
            if is_open!=should_open:
                issues.append(RegistryIssue('ERROR','FINDING_VIEW_DRIFT',f'{fid} status={o.status} in wrong view',view))

    generated=['00_HOME.md','CURRENT_STATE.md','CURRENT_TASK.md','CURRENT_BLOCKERS.md','CURRENT_PRIORITIES.md','findings/OPEN.md','findings/RESOLVED.md']
    generated += [str(p.relative_to(root)) for p in (root/'mocs').glob('*.md')]
    generated += [str(p.relative_to(root)) for p in (root/'views').glob('*.md')]
    for rel in generated:
        p=root/rel
        if not p.exists() or 'GENERATED BY SportsBrainMemory V1' not in p.read_text(encoding='utf-8'):
            issues.append(RegistryIssue('ERROR','GENERATED_VIEW_MARKER',f'{rel} missing generated marker',rel))

    secretp=[re.compile(r'\bsk-[A-Za-z0-9]{20,}\b'),re.compile(r'\bghp_[A-Za-z0-9]{20,}\b')]
    for p in root.rglob('*'):
        if not p.is_file() or any(part in {'.memory-build','.memory-backups','.git','.obsidian','_live','__pycache__'} for part in p.parts) or p.suffix not in {'.md','.json','.py'}:
            continue
        txt=p.read_text(encoding='utf-8',errors='ignore')
        for pat in secretp:
            if pat.search(txt):
                issues.append(RegistryIssue('ERROR','POSSIBLE_SECRET','secret-like token detected',str(p.relative_to(root))))

    return ValidationReport(profile,issues,len(reg.objects),len(reg.by_id),reg.status_counts())
