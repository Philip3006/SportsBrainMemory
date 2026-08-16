from __future__ import annotations
from pathlib import Path
import json, hashlib
from .registry import Registry
from .graph import Graph

def compile_shadow(root: Path, registry: Registry, graph: Graph) -> Path:
    build = root / ".memory-build" / "compiled"
    build.mkdir(parents=True, exist_ok=True)

    lines = []
    for obj in sorted(registry.objects, key=lambda o: (o.object_id or "~", o.relpath)):
        payload = {
            "id": obj.object_id,
            "type": obj.object_type,
            "path": obj.relpath,
            "status": obj.status,
            "canonical": obj.canonical,
            "sha256": hashlib.sha256((root / obj.path).read_bytes()).hexdigest(),
        }
        lines.append(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    (build / "OBJECT_INDEX.ndjson").write_text(
        "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
    )

    (build / "GRAPH.json").write_text(
        json.dumps(
            {
                "edges": [
                    {"source": e.source, "relation": e.relation, "target": e.target}
                    for e in graph.edges
                ],
                "issues": [i.__dict__ for i in graph.issues],
            },
            indent=2, sort_keys=True
        ) + "\n",
        encoding="utf-8",
    )
    return build
