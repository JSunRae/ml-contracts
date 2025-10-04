#!/usr/bin/env python3
"""Audit schemas and detect drift vs stored checksums.

Outputs validation/schema_audit.json and returns non-zero if drift detected.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
import os
from typing import Any, Dict

from validation_lib import (
    audit_schema,
    gather_schema_files,
    load_checksums,
    load_json,
    verify_drift,
    ensure_no_duplicate_properties,
)

BASE = Path(__file__).resolve().parent.parent
SCHEMA_DIR = Path(os.environ.get("SCHEMA_DIR_OVERRIDE", BASE / "schemas"))
CHECKSUM_DIR = Path(os.environ.get("CHECKSUM_DIR_OVERRIDE", BASE / "checksums"))
OUT_DIR = Path(os.environ.get("OUT_DIR_OVERRIDE", BASE / "validation"))


def describe() -> Dict[str, Any]:
    return {
        "name": "validate_schemas",
        "description": "Audit JSON Schemas for required/property counts and drift.",
        "inputs": {},
        "outputs": {"schema_audit.json": "Per-schema summary including drift flag."},
        "examples": ["python tools/validate_schemas.py", "python tools/validate_schemas.py --describe"]
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--describe", action="store_true")
    args = ap.parse_args()
    if args.describe:
        print(json.dumps(describe(), indent=2))
        return 0

    checksum_map = load_checksums(CHECKSUM_DIR)
    audits = []
    drift_count = 0
    for schema_file in gather_schema_files(SCHEMA_DIR):
        schema = load_json(schema_file)
        ensure_no_duplicate_properties(schema)
        aud = audit_schema(schema_file)
        stored = checksum_map.get(schema_file.name)
        drift, current_hash = verify_drift(schema_file, stored)
        audits.append({
            "file": schema_file.name,
            "schema_version": aud.schema_version,
            "required_count": aud.required_count,
            "properties_count": aud.properties_count,
            "structural_hash": current_hash,
            "stored_hash": stored,
            "drift": drift,
        })
        if drift:
            drift_count += 1

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "schema_audit.json").write_text(json.dumps({"schemas": audits, "drift_count": drift_count}, indent=2) + "\n", encoding="utf-8")
    if drift_count:
        print(f"Schema drift detected: {drift_count}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
