# Changelog

## Unreleased

Added
- contracts/policies/data_collection_policy_v1.json: canonical data collection policy (timezone, L2 window, calendar, lookbacks, symbol policy).
- contracts/fixtures/policy_v1.json and contracts/fixtures/export_manifest_with_policy.json examples.
- .github/copilot-instructions.md: consolidated Copilot scope/governance guidance.
- README.md: Table of Contents, Model Input Sequence definitions, Trading bars manifests documentation.
- schemas/bars_download_manifest.schema.json and schemas/bars_coverage_manifest.schema.json.
- contracts/fixtures/bars_download_manifest.sample.jsonl and contracts/fixtures/bars_coverage_manifest.sample.json.

Changed
- schemas/manifest.schema.json: optional `export_manifest.data_collection` block to record effective data-collection settings for reproducibility.
- contracts/README.md: add mini-TOC and clarify usage links.

Notes
- Backward compatible: no changes to required fields; no schema_version bump needed.
 - Trading bars manifests are standalone schemas; TF export manifest unchanged. Optional references under `export_manifest.data_lineage.*` remain allowed via `additionalProperties: true`.
