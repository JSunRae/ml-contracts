import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATE = ROOT / "tools" / "validate.py"
FIXTURES = ROOT / "contracts" / "fixtures"
SCHEMA_JSONL = ROOT / "schemas" / "bars_download_manifest.schema.json"
SCHEMA_COVERAGE = ROOT / "schemas" / "bars_coverage_manifest.schema.json"


def run_cmd(args):
    cmd = [sys.executable, str(VALIDATE)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def test_bars_jsonl_sample_validates_pass():
    code, out = run_cmd([
        "bars-jsonl",
        str(FIXTURES / "bars_download_manifest.sample.jsonl"),
        f"schema={SCHEMA_JSONL}",
    ])
    assert code == 0, out
    assert "Schema validation: PASS" in out
    assert "records=" in out


essential_fields = [
    "schema_version",
    "generated_at",
    "entries",
]


def test_bars_coverage_sample_validates_pass():
    code, out = run_cmd([
        "bars-coverage",
        str(FIXTURES / "bars_coverage_manifest.sample.json"),
        f"schema={SCHEMA_COVERAGE}",
    ])
    assert code == 0, out
    assert "Schema validation: PASS" in out
