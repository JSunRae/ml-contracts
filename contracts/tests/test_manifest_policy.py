import pathlib
import json
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/manifest.schema.json"
VALIDATE = ROOT / "tools/validate.py"
FIXTURES = ROOT / "contracts" / "fixtures"


def run_validate(manifest, policy=None):
    cmd = ["python", str(VALIDATE), str(manifest), f"schema={SCHEMA}"]
    if policy:
        cmd.insert(2, str(policy))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def test_old_manifest_validates_pass():
    code, out = run_validate(FIXTURES / "export_manifest_old.json")
    assert code == 0, out
    assert "Schema validation: PASS" in out


def test_new_manifest_with_policy_validates_pass_and_policy_ok():
    code, out = run_validate(
        FIXTURES / "export_manifest_with_policy.json",
        FIXTURES / "policy_v1.json",
    )
    assert code == 0, out
    assert "Schema validation: PASS" in out
    assert "Policy comparison: OK" in out


def test_policy_warning_on_difference():
    # modify one field on the fly: change l2_window
    manifest = json.loads((FIXTURES / "export_manifest_with_policy.json").read_text())
    manifest["export_manifest"]["data_collection"]["l2_window"] = "09:30-12:00"
    tmp = FIXTURES / "_tmp_manifest_diff.json"
    tmp.write_text(json.dumps(manifest))
    try:
        code, out = run_validate(tmp, FIXTURES / "policy_v1.json")
        assert code == 0, out
        assert "WARNING: data_collection.l2_window vs policy l2_window_default differs" in out or "l2_window vs policy" in out
    finally:
        if tmp.exists():
            tmp.unlink()
