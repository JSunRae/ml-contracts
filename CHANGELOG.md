# Changelog

## Unreleased

Added
- contracts/policies/data_collection_policy_v1.json: canonical data collection policy (timezone, L2 window, calendar, lookbacks, symbol policy).
- contracts/fixtures/policy_v1.json and contracts/fixtures/export_manifest_with_policy.json examples.
- .github/copilot-instructions.md: consolidated Copilot scope/governance guidance.
- README.md: Table of Contents, Model Input Sequence definitions, Trading bars manifests documentation.
- schemas/bars_download_manifest.schema.json and schemas/bars_coverage_manifest.schema.json.
- contracts/fixtures/bars_download_manifest.sample.jsonl and contracts/fixtures/bars_coverage_manifest.sample.json.
- schemas/manifest.schema.v2.json snapshot and manifest schema v2 requirements (dataset_version, feature_hash, calibration[ece/brier], latency/stability/regime diagnostics).
- fixtures/model_manifest_valid.json and fixtures/model_manifest_invalid_missing_field.json covering manifest v2 happy path + failure.
- Promotion rule thresholds for latency/stability/minority recall (`rules/promotion.rule.json`) plus tests.
- tools/validate.py auto-detects manifest schema version so legacy v1 manifests still validate without manual flags.

Changed
- schemas/manifest.schema.json: optional `export_manifest.data_collection` block to record effective data-collection settings for reproducibility.
- contracts/README.md: add mini-TOC and clarify usage links.
- BREAKING: Export manifest v2 now enforced as default schema. New required fields: `dataset_version`, `feature_hash`, `latency_metrics.{p50,p95,p99,max}`, `stability.{variance,max_regime_delta}`, `regime_metrics`, and `calibration.metrics` (`ece`, `brier`). Promotion rule updated to gate on these metrics.
- README.md / contracts/README.md: document manifest v2 required fields and promotion predicates.

Notes
- Legacy (`schema_version="v1"`) manifests still pass validation because `tools/validate.py` resolves the matching snapshot. Promotion gating will flip to “fail” once downstream repos migrate exporters and re-pin contracts.
- Trading bars manifests are standalone schemas; TF export manifest changes do not affect them.
- Tag the release `v2.0.0` once TF_1 + Trading validation CI are green.
