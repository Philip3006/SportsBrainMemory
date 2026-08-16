from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

@dataclass(frozen=True)
class Document:
    path: Path
    frontmatter: dict[str, Any]
    body: str
    raw: str

def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if not value:
        return ""
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    low = value.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none", "~"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [] if not inner else [_parse_scalar(p.strip()) for p in inner.split(",")]
    return value

def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    data: dict[str, Any] = {}
    current_list: str | None = None
    for lineno, raw in enumerate(text[4:end].splitlines(), start=2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("  - "):
            if not current_list:
                raise ValueError(f"line {lineno}: list item without list key")
            data[current_list].append(_parse_scalar(raw[4:]))
            continue
        if raw.startswith((" ", "\t")):
            raise ValueError(f"line {lineno}: nested mappings are outside the V1 canonical frontmatter subset")
        m = re.fullmatch(r"([A-Za-z0-9_-]+):(?:\s*(.*))?", raw)
        if not m:
            raise ValueError(f"line {lineno}: unsupported frontmatter syntax: {raw!r}")
        key, value = m.group(1), (m.group(2) or "").strip()
        if key in data:
            raise ValueError(f"line {lineno}: duplicate frontmatter key {key!r}")
        if value == "":
            data[key] = []
            current_list = key
        else:
            data[key] = _parse_scalar(value)
            current_list = None
    body = text[end + len("\n---\n"):]
    return data, body

def load_document(path: Path) -> Document:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(raw)
    return Document(path, meta, body, raw)
