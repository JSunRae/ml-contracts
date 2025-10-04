import json
from pathlib import Path
from validation_lib import classify_schema_change

BASE = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE / 'schemas' / 'manifest.schema.v1.json'


def test_breaking_change_detected():
    schema = json.loads(SCHEMA_PATH.read_text())
    # Remove a required field => breaking
    schema['required'].remove('data_hash')
    original = json.loads(SCHEMA_PATH.read_text())
    assert classify_schema_change(original, schema) == 'breaking'
