from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from .frontmatter import load_document
from .objects import MemoryObject

SKIP_DIRS = {".git", ".memory-build", ".memory-backups", "__pycache__", ".obsidian", "_live"}

@dataclass
class RegistryIssue:
    severity: str
    code: str
    message: str
    path: str | None = None

class Registry:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.objects = []
        self.by_id = {}
        self.issues = []

    def scan(self):
        self.objects, self.by_id, self.issues = [], {}, []
        seen = {}
        for path in sorted(self.root.rglob("*.md")):
            if any(part in SKIP_DIRS for part in path.relative_to(self.root).parts):
                continue
            rel = path.relative_to(self.root)
            try:
                doc = load_document(path)
            except Exception as exc:
                self.issues.append(RegistryIssue("ERROR","FRONTMATTER_PARSE",str(exc),rel.as_posix()))
                continue
            obj = MemoryObject.from_document(rel, doc.frontmatter, doc.body)
            self.objects.append(obj)
            if obj.object_id:
                if obj.object_id in seen:
                    self.issues.append(RegistryIssue(
                        "ERROR","DUPLICATE_ID",
                        f"{obj.object_id} declared in both {seen[obj.object_id]} and {rel.as_posix()}",
                        rel.as_posix()))
                else:
                    seen[obj.object_id] = rel.as_posix()
                    self.by_id[obj.object_id] = obj
        return self

    def status_counts(self):
        out = defaultdict(int)
        for obj in self.objects:
            out[obj.status or "NONE"] += 1
        return dict(sorted(out.items()))
