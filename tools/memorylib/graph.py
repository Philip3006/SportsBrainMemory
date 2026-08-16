from __future__ import annotations
from dataclasses import dataclass
from .registry import Registry, RegistryIssue

@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str

class Graph:
    def __init__(self, registry: Registry):
        self.registry = registry
        self.edges = []
        self.issues = []

    def build(self):
        self.edges, self.issues = [], []
        for obj in self.registry.objects:
            if not obj.object_id:
                continue
            for relation, targets in obj.relations.items():
                for target in targets:
                    self.edges.append(Edge(obj.object_id, relation, target))
                    if _looks_like_id(target) and target not in self.registry.by_id and relation != "invariants":
                        self.issues.append(RegistryIssue(
                            "ERROR","BROKEN_RELATION",
                            f"{obj.object_id} {relation} -> unknown id {target}",obj.relpath))
        return self

def _looks_like_id(value: str) -> bool:
    return "-" in value and " " not in value and "/" not in value and "#" not in value
