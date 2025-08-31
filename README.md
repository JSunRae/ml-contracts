# ml-contracts
Single source of truth for TF_1 ↔ Trading contracts.

## Contents
- schemas/manifest.schema.json — model export manifest (v1)
- rules/promotion.rule.json — JSON-Logic promotion thresholds
- fixtures/l2_fixture.csv / .parquet — tiny canonical L2/curated sample
- tools/validate.py — helper for CI/tests

## Versioning
Bump `schema_version` on breaking changes. Tag releases (v1.0.0, v2.0.0…).
