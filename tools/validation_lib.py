"""Core validation and schema change detection utilities for ml-contracts.

This module intentionally contains only pure functions operating on in-memory
Python data structures (dict/list primitives). No network or environment
specific dependencies. It is imported by validate_* CLI tools and tests.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write("\n")


def canonicalize(obj: Any) -> Any:
    """Return object with dictionaries recursively key-sorted.

    This ensures deterministic hashing independent of original key order.
    """
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [canonicalize(x) for x in obj]
    return obj


def compute_structural_hash(schema: Dict[str, Any]) -> str:
    """Compute a structural hash of a JSON Schema.

    We intentionally exclude description-only top-level keys that are clearly
    non-structural (e.g., 'title', 'description', '$id'). If those change alone,
    the hash should remain stable enabling PATCH documentation updates without
    bumping checksums.
    """
    exclude = {"title", "description", "$id"}
    pruned = {k: v for k, v in schema.items() if k not in exclude}
    canon = canonicalize(pruned)
    data = json.dumps(canon, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


@dataclass
class SchemaAudit:
    path: str
    schema_version: str | None
    required_count: int
    properties_count: int
    structural_hash: str


def extract_schema_version(schema: Dict[str, Any]) -> str | None:
    # Heuristic: look for 'schema_version' const in root properties or const values on root.
    if "properties" in schema and isinstance(schema["properties"], dict):
        sv = schema["properties"].get("schema_version")
        if isinstance(sv, dict) and "const" in sv:
            return str(sv["const"])
    # Alternate forms may embed schema_version as const at root (rare).
    if "schema_version" in schema and isinstance(schema["schema_version"], dict) and "const" in schema["schema_version"]:
        return str(schema["schema_version"]["const"])
    return None


def audit_schema(path: Path) -> SchemaAudit:
    schema = load_json(path)
    required_count = len(schema.get("required", []) or [])
    properties_count = len(schema.get("properties", {}) or {})
    structural_hash = compute_structural_hash(schema)
    return SchemaAudit(
        path=str(path),
        schema_version=extract_schema_version(schema),
        required_count=required_count,
        properties_count=properties_count,
        structural_hash=structural_hash,
    )


def classify_schema_change(old: Dict[str, Any], new: Dict[str, Any]) -> str:
    """Classify change type: 'none', 'additive', 'breaking', or 'other'.

    Currently simplistic: looks at required arrays and property key sets at root.
    Future: deep traversal with pointers.
    """
    old_req = set(old.get("required", []) or [])
    new_req = set(new.get("required", []) or [])
    old_props = set((old.get("properties") or {}).keys())
    new_props = set((new.get("properties") or {}).keys())

    # Removal of required property or any required property no longer present
    if not new_req.issuperset(old_req):
        return "breaking"
    # Detect property removals (even if not required) as breaking for conservative stance
    if not new_props.issuperset(old_props):
        return "breaking"
    # Additive optional: new props introduced but required unchanged
    if new_props != old_props:
        return "additive"
    # Required unchanged & props unchanged -> maybe description-only edits
    if compute_structural_hash(old) == compute_structural_hash(new):
        return "none"
    return "other"


def load_checksums(dir_path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    if not dir_path.exists():
        return result
    for f in dir_path.glob("*.sha256"):
        try:
            text = f.read_text(encoding="utf-8").strip()
            # Expect format: <hash>  <filename>
            if "  " in text:
                h, _ = text.split("  ", 1)
            else:
                h = text.split()[0]
            result[f.stem] = h
        except Exception:
            continue
    return result


def write_checksum(dir_path: Path, schema_file: Path, hash_hex: str) -> None:
    dir_path.mkdir(parents=True, exist_ok=True)
    out = dir_path / f"{schema_file.name}.sha256"
    out.write_text(f"{hash_hex}  {schema_file.name}\n", encoding="utf-8")


def verify_drift(schema_path: Path, stored_hash: str | None) -> Tuple[bool, str]:
    schema = load_json(schema_path)
    current = compute_structural_hash(schema)
    if stored_hash is None:
        return False, current  # No drift; baseline creation scenario.
    return current != stored_hash, current


def ensure_no_duplicate_properties(schema: Dict[str, Any]) -> None:
    # JSON objects cannot have duplicate keys after parsing, but nested 'required' arrays
    # may list duplicates; we enforce uniqueness there.
    def check_required(node: Any, path: str):
        if isinstance(node, dict):
            if "required" in node and isinstance(node["required"], list):
                req = node["required"]
                if len(req) != len(set(req)):
                    raise ValidationError(f"Duplicate entries in required array at {path}")
            for k, v in node.items():
                check_required(v, f"{path}/{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                check_required(v, f"{path}[{i}]")
    check_required(schema, "#")


def gather_schema_files(base: Path) -> List[Path]:
        """Return all schema files including versioned snapshots.

        Matches patterns:
            * *.schema.json (mutable current schemas)
            * *.schema.v*.json (immutable snapshots)
        """
        files: List[Path] = []
        files.extend([p for p in base.glob("*.schema.json")])
        files.extend([p for p in base.glob("*.schema.v*.json")])
        return sorted({p for p in files})


__all__ = [
    "ValidationError",
    "load_json",
    "dump_json",
    "canonicalize",
    "compute_structural_hash",
    "SchemaAudit",
    "audit_schema",
    "classify_schema_change",
    "load_checksums",
    "write_checksum",
    "verify_drift",
    "ensure_no_duplicate_properties",
    "gather_schema_files",
]
