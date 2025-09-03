# Changelog

## Unreleased

Added
- contracts/policies/data_collection_policy_v1.json: canonical data collection policy (timezone, L2 window, calendar, lookbacks, symbol policy).
- contracts/fixtures/policy_v1.json and contracts/fixtures/export_manifest_with_policy.json examples.

Changed
- schemas/manifest.schema.json: optional `export_manifest.data_collection` block to record effective data-collection settings for reproducibility.

Notes
- Backward compatible: no changes to required fields; no schema_version bump needed.
