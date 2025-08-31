import json, pathlib
from jsonschema import validate, Draft202012Validator
def _load(p): return json.loads(pathlib.Path(p).read_text())
def validate_manifest(manifest_path, schema_path):
    m, s = _load(manifest_path), _load(schema_path)
    Draft202012Validator.check_schema(s)
    validate(instance=m, schema=s)
    return True
