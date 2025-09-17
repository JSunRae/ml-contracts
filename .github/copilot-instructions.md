# Copilot Instructions: ml-contracts

This repository is contracts-only. It defines schemas, promotion rules, and canonical fixtures consumed by both TF_1 and Trading.

## Scope & Boundaries
- Allowed content:
  - JSON Schemas (e.g., `schemas/manifest.schema.json`)
  - JSON Logic rules (e.g., `rules/promotion.rule.json`)
  - Canonical fixtures (e.g., `fixtures/l2_fixture.parquet`, `fixtures/l2_fixture.csv`)
  - Governance docs (`README.md`, `CODEOWNERS`, this file)
- Not allowed:
  - Model code, trading code, notebooks, or general-purpose scripts
  - Duplicating schemas or rules outside their folders

## Governance & Versioning
- All schema/rule changes require:
  1. Review by CODEOWNERS (@JSunRae)
  2. Version bump inside JSON (e.g., `schema_version`) when required fields are added/removed
  3. Git tag update: `v1.x.y` for non-breaking, `v2.0.0` for breaking changes
- README must document versioning rules and release notes at a high level

## Documentation Rules
- Keep docs minimal and centralized:
  - `README.md`
  - `CODEOWNERS`
  - `.github/copilot-instructions.md`
- Append to README only to document schema/rule evolution or governance

## Testing & Validation
- Keep CSV and Parquet fixtures in sync (`fixtures/make_parquet.py` regenerates Parquet)
- Run tests locally before proposing schema changes:
  - `python3 -m pytest -q`
- Manifests can be validated and compared to policy:
  - `python3 tools/validate.py <manifest.json> schema=schemas/manifest.schema.json`
  - `python3 tools/validate.py <manifest.json> contracts/fixtures/policy_v1.json schema=schemas/manifest.schema.json`

## Agent Behaviour
- Do not suggest adding code outside schemas/rules/fixtures/docs
- For schema or rule edits, propose a minimal diff and mention the version/tag implications
- When required fields change, remind to bump `schema_version` and create a release tag
