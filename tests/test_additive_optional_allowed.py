import json
from pathlib import Path
from validation_lib import classify_schema_change

BASE = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE / 'schemas' / 'manifest.schema.v1.json'


def test_additive_optional():
    original = json.loads(SCHEMA_PATH.read_text())
    modified = json.loads(SCHEMA_PATH.read_text())
    modified['properties']['new_optional_field'] = {"type": "string"}
    # Not adding to required array -> additive
    assert classify_schema_change(original, modified) == 'additive'
