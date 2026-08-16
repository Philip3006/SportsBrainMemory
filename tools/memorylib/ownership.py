from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, re
from .registry import RegistryIssue

@dataclass
class OwnershipResult:
    claims: dict[str,list[str]]
    issues: list[RegistryIssue]

def _task_id(path):
    if not path.exists():
        return None
    m = re.search(r'(?m)^task_id:\s*"?([^"\n]+)"?\s*$', path.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else None

def analyze_known_v0_truth(root: Path):
    task = _task_id(root/"CURRENT_TASK.md")
    manifest_task = None
    mf = root/"_meta"/"memory_manifest.json"
    if mf.exists():
        try:
            manifest_task = json.loads(mf.read_text(encoding="utf-8")).get("current_task")
        except Exception:
            pass
    packet_task = None
    pp = root/"builder"/"CURRENT_CONTEXT_PACKET.md"
    if pp.exists():
        m = re.search(r'^\*\*Task:\*\*\s+([A-Za-z0-9_-]+)', pp.read_text(encoding="utf-8"), re.M)
        if m:
            packet_task = m.group(1)
    state_task = None
    sp = root/"CURRENT_STATE.md"
    if sp.exists():
        m = re.search(r'\|\s*Next Builder action\s*\|\s*`?([A-Za-z0-9_-]+)`?\s*\|', sp.read_text(encoding="utf-8"))
        if m:
            state_task = m.group(1)
    vals = [task, manifest_task, packet_task, state_task]
    claims = {"current_task":[
        f"CURRENT_TASK.md={task}",
        f"_meta/memory_manifest.json={manifest_task}",
        f"builder/CURRENT_CONTEXT_PACKET.md={packet_task}",
        f"CURRENT_STATE.md={state_task}",
    ]}
    issues = []
    if len({x for x in vals if x}) > 1:
        issues.append(RegistryIssue(
            "ERROR","CURRENT_TASK_CONTRADICTION",
            "current task is duplicated with conflicting values: " + "; ".join(claims["current_task"])
        ))
    return OwnershipResult(claims,issues)
