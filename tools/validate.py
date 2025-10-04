import json
import pathlib
import sys
from jsonschema import Draft202012Validator, Draft7Validator

def _load(p):
    return json.loads(pathlib.Path(p).read_text())

def _load_text(p: pathlib.Path) -> str:
    return pathlib.Path(p).read_text()


def _resolve_manifest_schema_path(manifest: dict, schema_path: pathlib.Path) -> pathlib.Path:
    """Return the schema path adjusted for manifest schema_version if available.

    Allows backward compatibility for older manifest versions by looking for
    sibling versioned schema snapshots such as manifest.schema.v1.json.
    """
    version = manifest.get("schema_version")
    if not version:
        return schema_path

    # Normalize to lowercase, but keep original for filename construction
    version_str = str(version).strip()
    if not version_str:
        return schema_path

    # If user already pointed at a versioned schema, keep it
    if f".{version_str}" in schema_path.name:
        return schema_path

    candidate_name = f"{schema_path.stem}.{version_str}{schema_path.suffix}"
    candidate = schema_path.with_name(candidate_name)
    if candidate.exists():
        return candidate

    return schema_path


def _choose_validator(schema: dict):
    """Pick a jsonschema Validator based on $schema meta.
    Defaults to Draft202012Validator; supports draft-07 for bars schemas.
    """
    meta = (schema.get("$schema") or "").lower()
    if "draft-07" in meta:
        Draft7Validator.check_schema(schema)
        return Draft7Validator
    # Fallback to 2020-12
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator


def _validate_instance(instance: dict, schema: dict):
    Validator = _choose_validator(schema)
    Validator(schema=schema).validate(instance)
    return True


def validate_manifest(manifest_path, schema_path):
    """
    Validate manifest against schema. Backward compatible: manifests without
    export_manifest.data_collection still pass.
    """
    schema_path_obj = pathlib.Path(schema_path)
    manifest = _load(manifest_path)
    resolved_schema_path = _resolve_manifest_schema_path(manifest, schema_path_obj)
    schema = _load(resolved_schema_path)
    _validate_instance(manifest, schema)
    return True


def validate_jsonl_per_line(jsonl_path: str, schema_path: str):
    """Validate a JSON Lines file where each line is a JSON object matching schema.
    Returns (ok: bool, count: int). Prints first error details to stdout on failure.
    """
    s = _load(schema_path)
    Validator = _choose_validator(s)

    count = 0
    for i, raw in enumerate(pathlib.Path(jsonl_path).read_text().splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"ERROR: line {i} is not valid JSON: {e}")
            return False, count
        try:
            Validator(schema=s).validate(obj)
        except Exception as e:
            print(f"ERROR: line {i} failed schema validation: {e}")
            return False, count
        count += 1
    return True, count

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
        print(
            "Usage:\n"
            "  Export manifest: validate.py <manifest.json> [policy.json] [schema=schemas/manifest.schema.json]\n"
            "  Bars JSONL:      validate.py bars-jsonl <bars_download_manifest.jsonl> [schema=schemas/bars_download_manifest.schema.json]\n"
            "  Bars coverage:   validate.py bars-coverage <bars_coverage_manifest.json> [schema=schemas/bars_coverage_manifest.schema.json]",
            file=sys.stderr,
        )
        return 2
    # Subcommands for bars schemas
    if argv[0] == "bars-jsonl":
        if len(argv) < 2:
            print("ERROR: missing JSONL path", file=sys.stderr)
            return 2
        jsonl_path = pathlib.Path(argv[1])
        schema_path = pathlib.Path("schemas/bars_download_manifest.schema.json")
        for arg in argv[2:]:
            if arg.startswith("schema="):
                schema_path = pathlib.Path(arg.split("=", 1)[1])
        ok, n = validate_jsonl_per_line(str(jsonl_path), str(schema_path))
        if not ok:
            return 1
        print(f"Schema validation: PASS (records={n})")
        return 0

    if argv[0] == "bars-coverage":
        if len(argv) < 2:
            print("ERROR: missing coverage JSON path", file=sys.stderr)
            return 2
        coverage_path = pathlib.Path(argv[1])
        schema_path = pathlib.Path("schemas/bars_coverage_manifest.schema.json")
        for arg in argv[2:]:
            if arg.startswith("schema="):
                schema_path = pathlib.Path(arg.split("=", 1)[1])
        validate_manifest(str(coverage_path), str(schema_path))
        print("Schema validation: PASS")
        return 0

    # Default path: export manifest validation (with optional policy compare)
    manifest_path = pathlib.Path(argv[0])
    policy_path = None
    schema_path = pathlib.Path("schemas/manifest.schema.json")
    for arg in argv[1:]:
        if arg.startswith("schema="):
            schema_path = pathlib.Path(arg.split("=", 1)[1])
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
