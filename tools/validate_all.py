#!/usr/bin/env python3
"""Run all contract validations and emit unified SUMMARY line.

SUMMARY {"schemas":N,"fixtures":M,"drift":D,"rule_errors":R,"invalid_examples":K,"duration_sec":X.Y}
Exit non-zero if drift>0 or rule_errors>0.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from promotion_rules import audit_rule_against_schema, RULE_PATH, MANIFEST_SCHEMA_PATH
from validation_lib import load_json

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = BASE / "validation"


def run_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def main() -> int:
    start = time.time()
    OUT_DIR.mkdir(exist_ok=True)
    # Schemas
    run_cmd(["python3", "tools/validate_schemas.py"])
    schema_audit = json.loads((OUT_DIR / "schema_audit.json").read_text())
    drift = schema_audit.get("drift_count", 0)

    # Fixtures
    run_cmd(["python3", "tools/validate_fixtures.py"])
    fixtures_audit = json.loads((OUT_DIR / "fixtures_audit.json").read_text())
    invalid_examples = fixtures_audit.get("invalid_examples", 0)

    # Promotion rule audit
    rule = load_json(RULE_PATH)
    schema = load_json(MANIFEST_SCHEMA_PATH)
    rule_audit = audit_rule_against_schema(rule, schema)
    (OUT_DIR / "promotion_rule_audit.json").write_text(json.dumps(rule_audit, indent=2) + "\n")
    rule_errors = 0 if rule_audit.get("valid") else 1

    summary = {
        "schemas": len(schema_audit.get("schemas", [])),
        "fixtures": len(fixtures_audit.get("fixtures", [])),
        "drift": drift,
        "rule_errors": rule_errors,
        "invalid_examples": invalid_examples,
        "duration_sec": round(time.time() - start, 3)
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("SUMMARY " + json.dumps(summary, separators=(",", ":")))
    exit_code = 0
    if drift or rule_errors:
        exit_code = 2
    return exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
