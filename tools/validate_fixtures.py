#!/usr/bin/env python3
"""Validate manifest fixtures against schema and basic parquet integrity.

Produces validation/fixtures_audit.json summarizing counts and any errors.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from validation_lib import load_json

try:  # pragma: no cover - import guard
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover
    jsonschema = None
try:  # pragma: no cover - optional
    import pyarrow as pa  # type: ignore
    import pyarrow.parquet as pq  # type: ignore
    import pyarrow.csv as pacsv  # type: ignore
except ImportError:  # pragma: no cover
    pa = pq = pacsv = None

BASE = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE / "schemas" / "manifest.schema.json"
FIXTURES = [
    BASE / "fixtures" / f
    for f in ("model_manifest_valid.json", "model_manifest_invalid_missing_field.json")
]
OUT_DIR = BASE / "validation"
L2_PARQUET = BASE / "fixtures" / "l2_fixture.parquet"
L2_CSV = BASE / "fixtures" / "l2_fixture.csv"
L2_SCHEMA = BASE / "schemas" / "level2_snapshot.schema.v1.json"


def describe() -> Dict[str, Any]:
    return {
        "name": "validate_fixtures",
        "description": "Validate model manifest fixtures against latest schema and parquet/csv integrity.",
        "inputs": {},
        "outputs": {"fixtures_audit.json": "Fixture validation results and dataset stats."},
        "examples": ["python tools/validate_fixtures.py"]
    }


def validate_manifest(schema: Dict[str, Any], manifest: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if jsonschema is None:
        return ["jsonschema library not installed"]
    validator = jsonschema.Draft7Validator(schema)  # type: ignore[attr-defined]
    for err in validator.iter_errors(manifest):
        errors.append(err.message)
    return errors


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--describe", action="store_true")
    args = ap.parse_args()
    if args.describe:
        print(json.dumps(describe(), indent=2))
        return 0

    schema = load_json(SCHEMA_PATH)
    results: List[Dict[str, Any]] = []
    invalid_examples = 0
    for fx in FIXTURES:
        manifest = load_json(fx)
        errs = validate_manifest(schema, manifest)
        ok = len(errs) == 0
        # Intentionally missing field fixture should be invalid
        if fx.name.startswith("model_manifest_invalid") and ok:
            errs.append("Expected invalid but passed")
            ok = False
        if not ok:
            invalid_examples += 1
        results.append({"fixture": fx.name, "valid": ok, "errors": errs})

    dataset_stats: Optional[Dict[str, Any]] = None
    if pa and pq and L2_PARQUET.exists():
        try:
            table = pq.read_table(L2_PARQUET)
            cols = table.schema
            dataset_stats = {
                "parquet_file": L2_PARQUET.name,
                "row_count": table.num_rows,
                "column_count": table.num_columns,
                "columns": [
                    {"name": name, "type": str(cols.field(i).type)} for i, name in enumerate(table.column_names)
                ],
            }
            # CSV cross-check
            if pacsv and L2_CSV.exists():
                csv_table = pacsv.read_csv(L2_CSV)
                dataset_stats["csv_row_count"] = csv_table.num_rows
                dataset_stats["csv_column_count"] = csv_table.num_columns
        except Exception as e:  # pragma: no cover
            dataset_stats = {"error": str(e)}
    else:
        dataset_stats = {"warning": "pyarrow not available or parquet missing"}

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "fixtures_audit.json").write_text(
        json.dumps({
            "fixtures": results,
            "invalid_examples": invalid_examples,
            "dataset": dataset_stats,
        }, indent=2) + "\n", encoding="utf-8")
    if invalid_examples:
        return 1  # Non-zero signals presence of expected invalids; caller may treat separately
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
