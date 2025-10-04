import json
from pathlib import Path
import jsonschema

BASE = Path(__file__).resolve().parent.parent
SCHEMA = json.load((BASE / 'schemas' / 'manifest.schema.json').open())
INVALID = json.load((BASE / 'fixtures' / 'model_manifest_invalid_missing_field.json').open())


def test_manifest_invalid_missing_field():
    validator = jsonschema.Draft7Validator(SCHEMA)
    errors = [e.message for e in validator.iter_errors(INVALID)]
    assert any('dataset_version' in e for e in errors)
