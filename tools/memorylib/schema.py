from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, re


# These two scalar keys are a deliberately small cross-object extension for
# the Obsidian visual layer. Their values are governed by
# tools/validate_visual_metadata.py rather than by every object schema.
VISUAL_METADATA_FIELDS = {'graph_domain', 'graph_role'}

@dataclass(frozen=True)
class SchemaIssue:
    code: str
    message: str
    severity: str = "ERROR"

class SchemaStore:
    def __init__(self, schema_dir: Path):
        self.schemas = {}
        if schema_dir.exists():
            for p in sorted(schema_dir.glob("*.json")):
                obj = json.loads(p.read_text(encoding="utf-8"))
                if obj.get("object_type"):
                    self.schemas[obj["object_type"]] = obj
    def get(self, object_type: str):
        return self.schemas.get(object_type)

def _matches(value: Any, typ: str) -> bool:
    return {
        "string": isinstance(value,str),
        "integer": isinstance(value,int) and not isinstance(value,bool),
        "number": isinstance(value,(int,float)) and not isinstance(value,bool),
        "boolean": isinstance(value,bool),
        "null": value is None,
        "array": isinstance(value,list),
    }.get(typ, False)

def validate_meta(meta, schema):
    issues = []
    for key in schema.get("required",[]):
        if key not in meta:
            issues.append(SchemaIssue("SCHEMA_MISSING_FIELD",f"missing required field {key!r}"))
    allowed = set(schema.get("properties",{}))
    if schema.get("additional_properties") is False:
        for key in meta:
            if key not in allowed and key not in VISUAL_METADATA_FIELDS:
                issues.append(SchemaIssue("SCHEMA_UNKNOWN_FIELD",f"unknown field {key!r}","WARNING"))
    for key,spec in schema.get("properties",{}).items():
        if key not in meta:
            continue
        value=meta[key]
        types=spec.get("type")
        if isinstance(types,str): types=[types]
        if types and not any(_matches(value,t) for t in types):
            issues.append(SchemaIssue("SCHEMA_BAD_TYPE",f"{key!r} must be {types}, got {type(value).__name__}"))
            continue
        if "enum" in spec and value not in spec["enum"]:
            issues.append(SchemaIssue("SCHEMA_BAD_ENUM",f"{key!r}={value!r} not in {spec['enum']}"))
        if isinstance(value,str) and spec.get("pattern") and not re.fullmatch(spec["pattern"],value):
            issues.append(SchemaIssue("SCHEMA_BAD_PATTERN",f"{key!r}={value!r} does not match {spec['pattern']!r}"))
    return issues
