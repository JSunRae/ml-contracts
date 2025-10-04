import json
from copy import deepcopy
from pathlib import Path
from promotion_rules import evaluate_rule, audit_rule_against_schema, RULE_PATH, MANIFEST_SCHEMA_PATH

BASE = Path(__file__).resolve().parent.parent

RULE = json.load(RULE_PATH.open())
SCHEMA = json.load(MANIFEST_SCHEMA_PATH.open())
VALID_MANIFEST = json.load((BASE / 'fixtures' / 'model_manifest_valid.json').open())


def test_rule_audit_valid():
    audit = audit_rule_against_schema(RULE, SCHEMA)
    assert audit['valid']
    assert audit['missing_metrics'] == []


def test_rule_pass_and_fail():
    assert evaluate_rule(RULE, VALID_MANIFEST) is True
    mutated = deepcopy(VALID_MANIFEST)
    mutated['metrics']['sharpe_sim']['value'] = 0.1  # below threshold
    assert evaluate_rule(RULE, mutated) is False

    mutated_latency = deepcopy(VALID_MANIFEST)
    mutated_latency['latency_metrics']['p95_ms']['value'] = 30.0
    assert evaluate_rule(RULE, mutated_latency) is False
