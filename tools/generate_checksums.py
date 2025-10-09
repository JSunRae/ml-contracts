#!/usr/bin/env python3
"""Generate structural hash checksums for schema snapshot files.

Writes each hash to checksums/<filename>.sha256 with format '<hash>  <filename>'.
Scans for files matching '*.schema.v*.json'.
"""
from __future__ import annotations

import sys
from pathlib import Path
from validation_lib import load_json, compute_structural_hash, write_checksum, dump_json
from export_manifest_hash import (
    compute_manifest_hash,
    DEFAULT_SCHEMA as MANIFEST_SCHEMA_PATH,
    DEFAULT_ARTIFACT as MANIFEST_ARTIFACT_PATH,
)

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"
CHECKSUM_DIR = Path(__file__).resolve().parent.parent / "checksums"


def main() -> int:
    snapshots = sorted(p for p in SCHEMA_DIR.glob("*.schema.v*.json"))
    if not snapshots:
        print("No snapshot schemas found", file=sys.stderr)
        return 1
    for schema_file in snapshots:
        schema = load_json(schema_file)
        h = compute_structural_hash(schema)
        write_checksum(CHECKSUM_DIR, schema_file, h)
        print(f"WROTE {schema_file.name}: {h}")

    hash_hex = compute_manifest_hash(MANIFEST_SCHEMA_PATH)
    dump_json(MANIFEST_ARTIFACT_PATH, {"schema": str(MANIFEST_SCHEMA_PATH), "sha256": hash_hex})
    print(f"WROTE manifest hash artifact: {hash_hex} -> {MANIFEST_ARTIFACT_PATH}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
