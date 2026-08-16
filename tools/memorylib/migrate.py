from __future__ import annotations
from pathlib import Path
import json
from .registry import Registry
from .ownership import analyze_known_v0_truth

PATH_RULES=[
("findings/records/","FIRST_CLASS_OBJECT"),("decisions/records/","FIRST_CLASS_OBJECT"),
("incidents/records/","FIRST_CLASS_OBJECT"),("invariants/","PRESERVE_DOMAIN_DEFINITIONS"),
("architecture/","PRESERVE_AND_ENRICH"),("domains/","PRESERVE_AND_ENRICH"),
("workstreams/","PRESERVE_AND_ENRICH"),("history/archive/","COLD_PRESERVE"),
("builder/CURRENT_CONTEXT_PACKET.md","GENERATED_ARTIFACT"),("findings/OPEN.md","GENERATED_VIEW"),
("findings/RESOLVED.md","GENERATED_VIEW"),("CURRENT_BLOCKERS.md","GENERATED_VIEW"),
("CURRENT_PRIORITIES.md","GENERATED_VIEW"),("CURRENT_STATE.md","GENERATED_VIEW_TARGET"),
("CURRENT_TASK.md","GENERATED_VIEW_TARGET"),("_meta/memory_manifest.json","REPLACE_WITH_GENERATED_INDEX"),
("README.md","STABLE_HUMAN_ENTRYPOINT"),("BOOTSTRAP.md","STABLE_AI_BOOTSTRAP")]

def classify(path):
    for prefix,cls in PATH_RULES:
        if path==prefix or path.startswith(prefix): return cls
    return "PRESERVE_REVIEW"

def dry_run(root:Path):
    build=root/".memory-build"/"migration"; build.mkdir(parents=True,exist_ok=True)
    registry=Registry(root).scan()
    rows=[{"path":o.relpath,"classification":classify(o.relpath),"id":o.object_id,"type":o.object_type,"status":o.status} for o in registry.objects]
    (build/"classification.ndjson").write_text("\n".join(json.dumps(r,sort_keys=True) for r in rows)+"\n",encoding="utf-8")
    conflicts=[i.__dict__ for i in analyze_known_v0_truth(root).issues]
    (build/"conflicts.json").write_text(json.dumps(conflicts,indent=2)+"\n",encoding="utf-8")
    counts={}
    for r in rows: counts[r["classification"]]=counts.get(r["classification"],0)+1
    plan={"migration":"v0-v1","mode":"dry-run","canonical_files_modified":0,
          "objects_scanned":len(registry.objects),"ids_scanned":len(registry.by_id),
          "classification_counts":counts,
          "blocking_conflicts":sum(1 for c in conflicts if c["severity"] in {"FATAL","ERROR"}),
          "principles":["preserve stable existing IDs","do not mutate canonical V0 during M1 dry-run",
                        "generated views stop owning volatile truth","zero active builder tasks is valid",
                        "external production truth must be reconciled before M2 cutover"]}
    (build/"plan.json").write_text(json.dumps(plan,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    report=["# SportsBrainMemory V0 → V1 Migration Dry Run","",
            f"- Objects scanned: **{plan['objects_scanned']}**",f"- IDs scanned: **{plan['ids_scanned']}**",
            "- Canonical files modified: **0**",f"- Blocking internal conflicts: **{plan['blocking_conflicts']}**",
            "","## Classification",""]
    report += [f"- {k}: {v}" for k,v in sorted(counts.items())]
    report += ["","## Conflicts",""]
    report += [f"- **{c['severity']} {c['code']}** — {c['message']}" for c in conflicts] or ["- None detected."]
    report += ["","## Cutover gate","",
               "M2 must not cut over generated current truth until current SportsBrain source/runtime/production evidence has been reconciled.",""]
    (build/"report.md").write_text("\n".join(report),encoding="utf-8")
    return build
