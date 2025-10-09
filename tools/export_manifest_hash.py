#!/usr/bin/env python3
"""Emit the canonical hash Trading/Win uses to validate export manifests."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

from validation_lib import canonicalize, dump_json, load_json

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCHEMA = ROOT / "schemas" / "manifest.schema.json"
DEFAULT_ARTIFACT = ROOT / "artifacts" / "current_manifest_hash.json"


def compute_manifest_hash(schema_path: Path = DEFAULT_SCHEMA) -> str:
    """Compute a deterministic sha256 over the canonical manifest schema JSON."""
    schema = load_json(schema_path)
    canonical = canonicalize(schema)
    payload = json.dumps(canonical, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_description() -> Dict[str, Any]:
    return {
        "name": "export_manifest_hash",
        "description": "Compute the canonical schema hash consumed by Trading for manifest validation.",
        "inputs": {
            "schema": "Optional path to manifest schema JSON (defaults to schemas/manifest.schema.json)",
            "flags": ["--describe", "--write-artifact", "--artifact-path"],
        },
        "outputs": {
            "stdout": "sha256 hash string",
            "artifact": "artifacts/current_manifest_hash.json when --write-artifact is provided",
        },
        "examples": [
            "python tools/export_manifest_hash.py",
            "python tools/export_manifest_hash.py --write-artifact",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the canonical hash for the manifest schema",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="Path to manifest schema JSON (defaults to schemas/manifest.schema.json)",
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help="Print JSON description and exit",
    )
    parser.add_argument(
        "--write-artifact",
        action="store_true",
        help="Write artifacts/current_manifest_hash.json and print hash",
    )
    parser.add_argument(
        "--artifact-path",
        type=Path,
        default=DEFAULT_ARTIFACT,
        help="Optional override for artifact output path (default artifacts/current_manifest_hash.json)",
    )
    args = parser.parse_args(argv)

    if args.describe:
        print(json.dumps(_build_description(), indent=2))
        return 0

    hash_hex = compute_manifest_hash(args.schema)
    print(hash_hex)

    if args.write_artifact:
        dump_json(args.artifact_path, {"schema": str(args.schema), "sha256": hash_hex})

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
