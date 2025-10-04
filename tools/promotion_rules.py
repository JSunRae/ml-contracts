#!/usr/bin/env python3
"""Evaluate promotion JSON Logic rule against a manifest metrics dict.

Also audits that all metric variable references exist in the provided schema.
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict
from typing import Any, Dict, List, Set

from validation_lib import load_json

RULE_PATH = Path(__file__).resolve().parent.parent / "rules" / "promotion.rule.json"
MANIFEST_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "manifest.schema.json"


class RuleError(Exception):
    pass


def _collect_vars(node: Any, acc: Set[str]) -> None:
    if isinstance(node, dict):
        if "var" in node and isinstance(node["var"], str):
            acc.add(node["var"])
        for v in node.values():
            _collect_vars(v, acc)
    elif isinstance(node, list):
        for v in node:
            _collect_vars(v, acc)


def referenced_variables(rule: Dict[str, Any]) -> Set[str]:
    vars: Set[str] = set()
    _collect_vars(rule, vars)
    return vars


def _section_properties(schema: Dict[str, Any], key: str) -> Set[str]:
    return set((schema.get("properties", {})
                .get(key, {})
                .get("properties", {}))
               .keys())


def audit_rule_against_schema(rule: Dict[str, Any], manifest_schema: Dict[str, Any]) -> Dict[str, Any]:
    refs = referenced_variables(rule)
    sections: Dict[str, Set[str]] = defaultdict(set)
    for ref in refs:
        parts = ref.split(".")
        if not parts:
            continue
        root = parts[0]
        if len(parts) > 1:
            sections[root].add(parts[1])
        else:
            sections[root].add("")

    missing: List[str] = []
    coverage: Dict[str, List[str]] = {}
    for root, names in sections.items():
        available = _section_properties(manifest_schema, root)
        if not available:
            coverage[root] = []
            continue
        missing_names = sorted(n for n in names if n and n not in available)
        if missing_names:
            missing.extend(f"{root}.{n}" for n in missing_names)
        coverage[root] = sorted(available)

    return {
        "referenced_vars": sorted(refs),
        "section_properties": coverage,
        "missing_metrics": missing,
        "valid": len(missing) == 0,
    }


def evaluate_rule(rule: Dict[str, Any], manifest: Dict[str, Any]) -> bool:
    """Evaluate a very small subset of JSON Logic used in promotion rule.

    Supported operators: and, >=, >, <=, <.
    """
    if not isinstance(rule, dict) or not rule:
        raise RuleError("Rule must be non-empty object")
    if "and" in rule:
        return all(evaluate_rule(r, manifest) for r in rule["and"])
    # Comparison ops have form {">=": [ {"var": "metrics.sharpe"}, 1.0 ]}
    for op in (">=", ">", "<=", "<"):
        if op in rule:
            arr = rule[op]
            if not (isinstance(arr, list) and len(arr) == 2):
                raise RuleError(f"Operator {op} expects 2-element list")
            left = _resolve_var(arr[0], manifest)
            right = _resolve_var(arr[1], manifest)
            if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                raise RuleError("Comparison operands must be numbers")
            if op == ">=":
                return left >= right
            if op == ">":
                return left > right
            if op == "<=":
                return left <= right
            if op == "<":
                return left < right
    raise RuleError(f"Unsupported rule segment: {rule}")


def _resolve_var(node: Any, manifest: Dict[str, Any]) -> Any:
    if isinstance(node, dict) and "var" in node:
        path = node["var"].split(".")
        cur: Any = manifest
        for p in path:
            if not isinstance(cur, dict) or p not in cur:
                raise RuleError(f"Variable path not found: {node['var']}")
            cur = cur[p]
        return cur
    return node


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Evaluate promotion rule against manifest JSON")
    ap.add_argument("manifest", type=Path, help="Path to manifest JSON to evaluate")
    ap.add_argument("--describe", action="store_true", help="Print JSON description and exit")
    args = ap.parse_args()

    if args.describe:
        desc = {
            "name": "promotion_rules",
            "description": "Evaluate promotion rule JSON Logic against a manifest file.",
            "inputs": {"manifest": "Path to manifest JSON file"},
            "outputs": {"stdout": "PASS/FAIL line and JSON audit"},
            "examples": ["python tools/promotion_rules.py fixtures/model_manifest_valid.json"]
        }
        print(json.dumps(desc, indent=2))
        return 0

    manifest = load_json(args.manifest)
    rule = load_json(RULE_PATH)
    schema = load_json(MANIFEST_SCHEMA_PATH)
    audit = audit_rule_against_schema(rule, schema)
    if not audit["valid"]:
        print(json.dumps({"error": "missing metrics", **audit}, indent=2))
        return 2
    try:
        passed = evaluate_rule(rule, manifest)
    except RuleError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 3
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
