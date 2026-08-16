from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RELATION_KEYS = {
    "depends_on","related","invariants","findings","decisions","evidence","tested_by",
    "verified_by","governed_by","writes","reads","publishes","consumes","triggered_by",
    "executes_on","resolves","supersedes","superseded_by","blocks","blocked_by",
    "belongs_to","implements","exposes","stores","derived_from","feeds",
}

@dataclass
class MemoryObject:
    path: Path
    meta: dict[str, Any]
    body: str
    object_id: str | None = None
    object_type: str | None = None
    status: str | None = None
    canonical: bool | None = None
    relations: dict[str, list[str]] = field(default_factory=dict)

    @property
    def relpath(self) -> str:
        return self.path.as_posix()

    @classmethod
    def from_document(cls, relpath: Path, meta: dict[str, Any], body: str) -> "MemoryObject":
        relations = {}
        for key in RELATION_KEYS:
            value = meta.get(key)
            if isinstance(value, list):
                relations[key] = [str(v) for v in value]
            elif isinstance(value, str) and value:
                relations[key] = [value]
        return cls(
            path=relpath, meta=meta, body=body,
            object_id=str(meta["id"]) if meta.get("id") not in (None, "") else None,
            object_type=str(meta["type"]) if meta.get("type") not in (None, "") else None,
            status=str(meta["status"]) if meta.get("status") not in (None, "") else None,
            canonical=meta.get("canonical") if isinstance(meta.get("canonical"), bool) else None,
            relations=relations,
        )
