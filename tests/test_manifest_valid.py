import json
from pathlib import Path
import jsonschema

BASE = Path(__file__).resolve().parent.parent
SCHEMA = json.load((BASE / 'schemas' / 'manifest.schema.json').open())
VALID = json.load((BASE / 'fixtures' / 'model_manifest_valid.json').open())


def test_manifest_valid_passes():
    validator = jsonschema.Draft7Validator(SCHEMA)
    errors = list(validator.iter_errors(VALID))
    assert errors == []
