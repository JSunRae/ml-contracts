import json
import pathlib
import sys
from jsonschema import validate, Draft202012Validator

def _load(p):
    return json.loads(pathlib.Path(p).read_text())

def validate_manifest(manifest_path, schema_path):
    """
    Validate manifest against schema. Backward compatible: manifests without
    export_manifest.data_collection still pass.
    """
    m, s = _load(manifest_path), _load(schema_path)
    Draft202012Validator.check_schema(s)
    validate(instance=m, schema=s)
    return True

def load_policy(policy_path):
    """Load data collection policy JSON."""
    return _load(policy_path)

def compare_manifest_to_policy(manifest_path, policy_path):
    """
    Compare export_manifest.data_collection fields in manifest to canonical policy.
    Returns a list of human-readable warnings for any differences. Does not fail.
    """
    m = _load(manifest_path)
    policy = _load(policy_path)
    dc = (
        m.get("export_manifest", {})
         .get("data_collection", {})
    )
    warnings = []
    if not dc:
        warnings.append("manifest has no export_manifest.data_collection block; cannot compare to policy")
        return warnings

    # Field mappings: manifest -> policy
    checks = [
        (dc.get("policy_version"), policy.get("policy_version"), "policy_version"),
        (dc.get("session_timezone"), policy.get("session_timezone"), "session_timezone"),
        (dc.get("l2_window"), policy.get("l2_window_default"), "l2_window vs policy l2_window_default"),
        (dc.get("bar_lookbacks"), policy.get("recommended_bar_lookbacks"), "bar_lookbacks vs policy recommended_bar_lookbacks"),
        (dc.get("symbol_policy_version"), policy.get("symbol_policy", {}).get("version"), "symbol_policy_version"),
    ]
    for manifest_val, policy_val, name in checks:
        if manifest_val is None or policy_val is None:
            continue
        if manifest_val != policy_val:
            warnings.append(f"data_collection.{name} differs from policy (manifest={manifest_val} policy={policy_val})")

    return warnings

def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv or argv[0] in {"-h", "--help"}:
        print("Usage: validate.py <manifest.json> [policy.json] [schema=schemas/manifest.schema.json]", file=sys.stderr)
        return 2

    manifest_path = pathlib.Path(argv[0])
    policy_path = None
    schema_path = pathlib.Path("schemas/manifest.schema.json")
    for arg in argv[1:]:
        if arg.startswith("schema="):
            schema_path = pathlib.Path(arg.split("=",1)[1])
        else:
            policy_path = pathlib.Path(arg)

    validate_manifest(str(manifest_path), str(schema_path))
    print("Schema validation: PASS")

    if policy_path and policy_path.exists():
        warnings = compare_manifest_to_policy(str(manifest_path), str(policy_path))
        for w in warnings:
            print(f"WARNING: {w}")
        if not warnings:
            print("Policy comparison: OK (no differences)")

if __name__ == "__main__":
    raise SystemExit(main())
